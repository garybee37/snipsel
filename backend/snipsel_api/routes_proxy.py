from __future__ import annotations

import json
from urllib import request as urllib_request
from urllib import parse as urllib_parse
from urllib.error import URLError, HTTPError

from flask import Blueprint, request
from snipsel_api.auth_session import json_response, require_auth
from snipsel_api.errors import api_error
from functools import lru_cache

proxy_bp = Blueprint("proxy", __name__)

# Cache metadata for 1 hour (using a simple lru_cache for in-process memory)
# Note: In a multi-worker production environment, Redis or similar would be better.
@lru_cache(maxsize=1000)
def _fetch_deezer_metadata(url: str) -> dict:
    req = urllib_request.Request(url, headers={"User-Agent": "Snipsel/1.0"})
    with urllib_request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))

@lru_cache(maxsize=1000)
def _resolve_deezer_url(short_url: str) -> str:
    req = urllib_request.Request(short_url, headers={"User-Agent": "Snipsel/1.0"})
    with urllib_request.urlopen(req, timeout=10) as response:
        return response.geturl()

@lru_cache(maxsize=1000)
def _fetch_youtube_metadata(oembed_url: str) -> dict:
    req = urllib_request.Request(oembed_url, headers={"User-Agent": "Snipsel/1.0"})
    with urllib_request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))

DEEZER_API_BASE = "https://api.deezer.com"

@proxy_bp.route("/deezer", methods=["GET"])
@require_auth
def proxy_deezer():
    """Proxy requests to Deezer API to avoid CORS issues."""
    media_type = request.args.get("type") # track, album, artist
    media_id = request.args.get("id")
    short_url = request.args.get("url")

    if short_url:
        # Resolve short link (e.g. link.deezer.com)
        try:
            resolved_url = _resolve_deezer_url(short_url)
            # URL structure: https://www.deezer.com/{locale}/{type}/{id} or https://www.deezer.com/{type}/{id}
            parts = resolved_url.split("/")
            # Filter out empty strings from trailing slashes or multiple slashes
            parts = [p for p in parts if p]
            
            # Look for track/album/artist
            for i, part in enumerate(parts):
                if part in ["track", "album", "artist"] and i + 1 < len(parts):
                    media_type = part
                    media_id = parts[i+1].split("?")[0] # strip query params
                    break
        except Exception as e:
            raise api_error(502, "external_error", f"Failed to resolve Deezer link: {str(e)}")

    if not media_type or not media_id:
        raise api_error(400, "invalid_input", "type and id (or a valid url) are required")
    
    if media_type not in ["track", "album", "artist"]:
        raise api_error(400, "invalid_input", "invalid media type")

    url = f"{DEEZER_API_BASE}/{media_type}/{media_id}"
    
    try:
        data = _fetch_deezer_metadata(url)
        if "error" in data:
            return json_response(data, status=400)
        return json_response(data)
    except HTTPError as e:
        return json_response({"error": str(e)}, status=e.code)
    except URLError as e:
        raise api_error(502, "external_error", f"Failed to connect to Deezer: {str(e)}")
    except Exception as e:
        raise api_error(500, "internal_error", str(e))

@proxy_bp.route("/youtube", methods=["GET"])
@require_auth
def proxy_youtube():
    """Proxy requests to YouTube oEmbed API."""
    video_url = request.args.get("url")
    if not video_url:
        raise api_error(400, "invalid_input", "url is required")

    # YouTube oEmbed endpoint
    oembed_url = f"https://www.youtube.com/oembed?url={urllib_parse.quote(video_url)}&format=json"

    try:
        data = _fetch_youtube_metadata(oembed_url)
        return json_response(data)
    except HTTPError as e:
        return json_response({"error": str(e)}, status=e.code)
    except URLError as e:
        raise api_error(502, "external_error", f"Failed to connect to YouTube: {str(e)}")
    except Exception as e:
        raise api_error(500, "internal_error", str(e))
