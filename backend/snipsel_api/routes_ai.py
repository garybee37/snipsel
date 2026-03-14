from __future__ import annotations

import json
from urllib import request as urllib_request
from urllib.error import URLError, HTTPError

from flask import Blueprint, request
from snipsel_api.auth_session import json_response, require_auth, current_user
from snipsel_api.errors import api_error

ai_bp = Blueprint("ai", __name__)

@ai_bp.post("/generate")
@require_auth
def generate():
    user = current_user()
    if not user.ai_llm_url or not user.ai_api_key:
        raise api_error(400, "ai_not_configured", "AI settings are not fully configured")

    data = request.get_json() or {}
    prompt = data.get("prompt")
    context = data.get("context", "")
    
    if not prompt:
        raise api_error(400, "invalid_input", "Prompt is required")

    model = user.ai_model_name or "gpt-3.5-turbo"
    
    # OpenAI compatible payload
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant integrated into a note-taking app called Snipsel. Help the user with their notes."},
            {"role": "user", "content": f"Context/Note content:\n{context}\n\nTask: {prompt}"}
        ]
    }

    try:
        req = urllib_request.Request(
            user.ai_llm_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {user.ai_api_key}"
            },
            method="POST"
        )
        with urllib_request.urlopen(req, timeout=30) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            # Expecting OpenAI format
            if "choices" in res_data and len(res_data["choices"]) > 0:
                ai_text = res_data["choices"][0]["message"]["content"]
                return json_response({"text": ai_text})
            else:
                return json_response({"error": "Unexpected response format from LLM", "details": res_data}, status=502)

    except HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            error_json = json.loads(error_body)
            return json_response({"error": f"LLM Error: {e.code}", "details": error_json}, status=e.code)
        except:
            return json_response({"error": f"LLM Error: {e.code}", "details": error_body}, status=e.code)
    except URLError as e:
        raise api_error(502, "external_error", f"Failed to connect to LLM: {str(e)}")
    except Exception as e:
        raise api_error(500, "internal_error", str(e))
