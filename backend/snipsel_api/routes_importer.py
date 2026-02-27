from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from urllib import request as urllib_request
from urllib.error import URLError, HTTPError

from flask import Blueprint, current_app
from PIL import Image

from snipsel_api.auth_session import current_user, json_response, require_auth
from snipsel_api.errors import ApiError, api_error
from snipsel_api.extensions import db
from snipsel_api.models import (
    Attachment,
    Collection,
    CollectionFavorite,
    CollectionSnipsel,
    Snipsel,
    SnipselCollectionRef,
)

importer_bp = Blueprint("importer", __name__)

TWO_S_BASE_URL = "https://twosapp.com"


def _twos_api_request(endpoint: str, data: dict | None = None) -> dict:
    """Make a request to the TwoS API using urllib."""
    url = f"{TWO_S_BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}

    if data:
        body = json.dumps(data).encode("utf-8")
        req = urllib_request.Request(url, data=body, headers=headers, method="POST")
    else:
        req = urllib_request.Request(url, headers=headers)

    try:
        with urllib_request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"[TwoS Import] API error {e.code}: {error_body}")
        raise api_error(e.code, "external_error", f"TwoS API error: {error_body}")
    except URLError as e:
        raise api_error(502, "external_error", f"Failed to connect to TwoS: {str(e)}")


def _download_image(url: str) -> bytes | None:
    """Download an image from URL using urllib."""
    try:
        req = urllib_request.Request(url, headers={"User-Agent": "Snipsel/1.0"})
        with urllib_request.urlopen(req, timeout=30) as response:
            return response.read()
    except (URLError, HTTPError) as e:
        print(f"[TwoS Import] Failed to download image {url}: {e}")
        return None


def _write_thumbnail(src_path: Path, dst_path: Path) -> None:
    """Create a thumbnail from an image with EXIF orientation handling."""
    if Image is None:
        return
    try:
        with Image.open(src_path) as im:
            # Handle EXIF orientation for phone photos
            try:
                exif = im.getexif()
                if exif:
                    orientation = exif.get(0x0112)  # Orientation tag
                    if orientation == 3:
                        im = im.rotate(180, expand=True)
                    elif orientation == 6:
                        im = im.rotate(270, expand=True)
                    elif orientation == 8:
                        im = im.rotate(90, expand=True)
            except Exception:
                pass  # EXIF handling is best-effort

            im.thumbnail((512, 512))
            im = im.convert("RGB")
            im.save(dst_path, format="JPEG", quality=80)
    except Exception as e:
        print(f"[TwoS Import] Failed to create thumbnail: {e}")


def _download_and_create_attachment(photo_url: str, snipsel_id: str, user_id: str, index: int) -> Attachment | None:
    """Download a photo and create an attachment record."""
    upload_dir = Path(current_app.config.get("SNIPSEL_UPLOAD_DIR", "./uploads"))
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Download the image
    image_data = _download_image(photo_url)
    if not image_data:
        return None

    # Generate filename from URL or use index
    att_id = str(uuid.uuid4())
    url_filename = os.path.basename(photo_url.split("?")[0])
    if url_filename and "." in url_filename:
        ext = url_filename.rsplit(".", 1)[-1][:10]
        safe_name = f"photo_{index}.{ext}"
    else:
        safe_name = f"photo_{index}.jpg"

    storage_path = upload_dir / f"{att_id}_{safe_name}"

    # Save the image
    with open(storage_path, "wb") as f:
        f.write(image_data)

    size = storage_path.stat().st_size

    # Determine mime type
    mime_type = "image/jpeg"
    if safe_name.lower().endswith(".png"):
        mime_type = "image/png"
    elif safe_name.lower().endswith(".gif"):
        mime_type = "image/gif"
    elif safe_name.lower().endswith(".webp"):
        mime_type = "image/webp"

    # Create thumbnail
    thumbnail_path: Path | None = None
    if mime_type.startswith("image/"):
        thumbnail_path = upload_dir / f"{att_id}_thumb.jpg"
        _write_thumbnail(storage_path, thumbnail_path)

    # Create attachment record
    att = Attachment(
        id=att_id,
        snipsel_id=snipsel_id,
        filename=safe_name,
        mime_type=mime_type,
        size_bytes=size,
        storage_path=str(storage_path),
        thumbnail_path=str(thumbnail_path) if thumbnail_path else None,
        created_by_id=user_id,
    )
    db.session.add(att)
    return att


@importer_bp.route("/twos/login", methods=["POST"])
@require_auth
def twos_login():
    """Authenticate with TwoS and return user info and token."""
    from flask import request

    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        raise api_error(400, "invalid_input", "username and password are required")

    try:
        result = _twos_api_request(
            "/apiV2/user/login/new",
            data={"user": {"username": username, "password": password}},
        )

        if "user" not in result:
            raise api_error(401, "auth_failed", "Login failed")

        user_data = result["user"]
        return json_response(
            {
                "user": {
                    "id": user_data.get("_id"),
                    "username": user_data.get("username"),
                    "token": user_data.get("token"),
                }
            }
        )
    except ApiError:
        raise
    except Exception as e:
        raise api_error(502, "external_error", f"Failed to connect to TwoS: {str(e)}")


@importer_bp.route("/twos/lists", methods=["POST"])
@require_auth
def twos_lists():
    """Get all lists from TwoS via fullSync endpoint."""
    from flask import request

    data = request.get_json() or {}
    token = data.get("token")
    user_id = data.get("userId")
    last_sync = data.get("lastSync", "0")

    if not token:
        raise api_error(401, "auth_required", "TwoS token required")
    if not user_id:
        raise api_error(400, "invalid_input", "userId required")

    try:
        # Use fullSync endpoint as specified
        result = _twos_api_request(
            "/apiV2/user/fullSync",
            data={"lastSync": last_sync, "user_id": user_id, "token": token},
        )

        # Parse entries from fullSync response
        lists_data = result.get("entries") or result.get("lists", [])

        lists = [
            {
                "id": lst.get("_id"),
                "name": lst.get("title") or lst.get("name", "Untitled"),
                "emoji": lst.get("emoji"),
                "favorited": lst.get("favorited", False),
                "isDaily": lst.get("today", False),
                "coverPhoto": lst.get("coverPhoto"),
                "thingsCount": len(lst.get("things", [])),
            }
            for lst in lists_data
        ]

        return json_response({"lists": lists})
    except ApiError:
        raise
    except Exception as e:
        raise api_error(502, "external_error", f"Failed to fetch lists: {str(e)}")


@importer_bp.route("/twos/import", methods=["POST"])
@require_auth
def twos_import():
    """Import selected lists from TwoS."""
    from flask import request

    user = current_user()
    data = request.get_json() or {}

    list_ids = data.get("listIds", [])
    token = data.get("token")
    user_id = data.get("userId")

    if not list_ids:
        raise api_error(400, "invalid_input", "listIds required")
    if not token:
        raise api_error(401, "auth_required", "TwoS token required")
    if not user_id:
        raise api_error(400, "invalid_input", "userId required")

    print(f"[TwoS Import] ==> Starting import of {len(list_ids)} lists...")

    # Track imported collection IDs for subEntry references
    imported_collection_ids: dict[str, str] = {}  # twos_list_id -> snipsel_collection_id

    imported = 0
    skipped = 0
    errors = []

    for list_id in list_ids:
        print(f"[TwoS Import] Fetching list {list_id}...")
        try:
            success = import_list_with_id(user, data, list_id)

            db.session.commit()
            if success:
                imported += 1

            print(f"[TwoS Import]   Completed: {list_id}")

        except Exception as e:
            db.session.rollback()
            error_msg = f"Failed to import list '{list_id}': {str(e)}"
            print(f"[TwoS Import] ERROR: {error_msg}")
            errors.append(error_msg)

    print(f"[TwoS Import] <== Finished import: {imported} imported, {skipped} skipped")
    if errors:
        print(f"[TwoS Import] Errors: {errors}")
    print("[TwoS Import] IMPORT COMPLETE")

    return json_response(
        {
            "imported": imported,
            "skipped": skipped,
            "errors": errors,
        }
    )


def import_list_with_id(user, data, list_id) -> str:
    overwrite = data.get("overwrite", False)
    token = data.get("token")
    user_id = data.get("userId")
    # Fetch individual list via /apiV2/entry/{_id}
    try:
        result = _twos_api_request(
            f"/apiV2/entry/{list_id}",
            data={"noPush": True, "user_id": user_id, "token": token},
        )
    except ApiError as e:
        # errors.append(f"Failed to fetch list {list_id}: {e.message}")
        print(f"[TwoS Import] ERROR: Failed to fetch list {list_id}: {e.message}")
        return None
    except Exception as e:
        # errors.append(f"Failed to fetch list {list_id}: {str(e)}")
        print(f"[TwoS Import] ERROR: Failed to fetch list {list_id}: {str(e)}")
        return None

    lst = result.get("entry", result)  # Response may have "entry" wrapper or be direct
    list_name = lst.get("title", "Untitled")
    print(f"[TwoS Import] Importing list: {list_name}")

    try:
        # Check if collection already exists
        existing = (
            db.session.execute(
                db.select(Collection).where(
                    Collection.owner_user_id == user.id,
                    Collection.title == list_name,
                    Collection.deleted_at.is_(None),
                )
            )
            .scalars()
            .first()
        )

        if existing:
            if overwrite:
                existing.deleted_at = db.func.now()
                db.session.commit()
            else:
                print(f"[TwoS Import] Skipping existing list: {list_name}")
                # skipped += 1
                return None

        # Create collection with metadata from TwoS
        emoji = lst.get("emoji") or "📝"
        cover_photo = lst.get("coverPhoto")

        collection = Collection(
            owner_user_id=user.id,
            title=list_name,
            icon=emoji[:8] if emoji else "📝",  # Limit to 8 chars
            header_image_url=cover_photo if cover_photo else None,
            created_by_id=user.id,
            modified_by_id=user.id,
        )

        db.session.add(collection)
        db.session.flush()

        # Store mapping for subEntry references
        # imported_collection_ids[lst.get("_id")] = collection.id

        # Handle favorited status
        if lst.get("favorited"):
            favorite = CollectionFavorite(
                user_id=user.id,
                collection_id=collection.id,
            )
            db.session.add(favorite)

        # Import things as snipsels
        things = result.get("posts", [])
        print(f"[TwoS Import] ==>   {len(things)} tings found...")
        for idx, thing in enumerate(things):
            body = thing.get("text", "")
            post_type = thing.get("type", "text")
            photos = thing.get("photos", [])
            print(thing)

            # Determine snipsel type and content
            snipsel_type = "text"
            content_parts = []

            # Handle header formatting
            if thing.get("header"):
                content_parts.append(f"# {body}")
            elif thing.get("subheader"):
                content_parts.append(f"## {body}")
            else:
                content_parts.append(body)

            # Determine type based on post type
            if post_type == "checkbox" or thing.get("isComplete") is not None:
                snipsel_type = "task"

            if len(photos) > 0:
                snipsel_type = "image"
            # Links are imported as text with markdown format

            # Handle tags
            tags = thing.get("tags", [])
            if tags:
                tag_str = ", ".join(f"#{tag}" for tag in tags if tag)
                if tag_str:
                    content_parts.append("")  # Blank line before tags
                    content_parts.append(tag_str)

            # Handle URL - append as markdown link
            url = thing.get("url")
            if url:
                content_parts.append(f"({url})")

            # Handle subEntry - create wiki link reference
            if thing.get("subEntry_id"):
                # The subEntry contains a reference to another list
                # We'll create a [[wiki link]] style reference
                content_parts = [f"[[{body}]]"]

            final_content = "\n".join(content_parts)

            snipsel = Snipsel(
                owner_user_id=user.id,
                type=snipsel_type,
                content_markdown=final_content,
                task_done=thing.get("isComplete", False),
                created_by_id=user.id,
                modified_by_id=user.id,
            )
            db.session.add(snipsel)
            db.session.flush()

            # Download and attach photos
            if photos:
                print(f"[TwoS Import]   Downloading {len(photos)} photos for snipsel...")
                for photo_idx, photo_url in enumerate(photos):
                    if photo_url and isinstance(photo_url, str):
                        _download_and_create_attachment(photo_url, snipsel.id, user.id, photo_idx + 1)

            # Link snipsel to collection
            cs = CollectionSnipsel(
                collection_id=collection.id,
                snipsel_id=snipsel.id,
                position=idx + 1,
                indent=0,
            )
            db.session.add(cs)
            db.session.flush()

            # Handle subEntry - create SnipselCollectionRef
            if thing.get("subEntry_id"):
                ref_list_id = thing.get("subEntry_id")
                list_id = import_list_with_id(user, data, ref_list_id)
                ref = SnipselCollectionRef(
                    snipsel_id=snipsel.id,
                    collection_id=list_id,
                )
                db.session.add(ref)
                db.session.flush()

    except Exception as e:
        print(e)
    return collection.id
