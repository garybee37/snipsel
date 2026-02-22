from __future__ import annotations

import os
import uuid
from pathlib import Path

from flask import Blueprint, current_app, request, send_file
from PIL import Image

from snipsel_api.auth_session import current_user, json_response, require_auth
from snipsel_api.errors import api_error
from snipsel_api.extensions import db
from snipsel_api.models import Attachment, Snipsel

attachments_bp = Blueprint("attachments", __name__)


@attachments_bp.post("/snipsels/<snipsel_id>/attachments")
@require_auth
def upload_attachment(snipsel_id: str):
    user = current_user()
    snipsel = db.session.get(Snipsel, snipsel_id)
    if not snipsel or snipsel.owner_user_id != user.id or snipsel.deleted_at is not None:
        raise api_error(404, "not_found", "Snipsel not found")

    if "file" not in request.files:
        raise api_error(400, "invalid_input", "file is required")

    file = request.files["file"]
    if not file or not file.filename:
        raise api_error(400, "invalid_input", "file is required")

    upload_dir = Path(current_app.config.get("SNIPSEL_UPLOAD_DIR", "./uploads"))
    upload_dir.mkdir(parents=True, exist_ok=True)

    att_id = str(uuid.uuid4())
    safe_name = os.path.basename(file.filename)
    storage_path = upload_dir / f"{att_id}_{safe_name}"

    file.save(storage_path)
    size = storage_path.stat().st_size
    mime_type = file.mimetype

    thumbnail_path: Path | None = None
    if mime_type and mime_type.startswith("image/"):
        thumbnail_path = upload_dir / f"{att_id}_thumb.jpg"
        _write_thumbnail(storage_path, thumbnail_path)

    att = Attachment(
        id=att_id,
        snipsel_id=snipsel.id,
        filename=safe_name,
        mime_type=mime_type,
        size_bytes=size,
        storage_path=str(storage_path),
        thumbnail_path=str(thumbnail_path) if thumbnail_path else None,
        created_by_id=user.id,
    )
    db.session.add(att)
    db.session.commit()

    return json_response(
        {
            "attachment": {
                "id": att.id,
                "filename": att.filename,
                "mime_type": att.mime_type,
                "size_bytes": att.size_bytes,
                "has_thumbnail": att.thumbnail_path is not None,
            }
        },
        status=201,
    )


@attachments_bp.get("/attachments/<attachment_id>")
@require_auth
def download_attachment(attachment_id: str):
    user = current_user()
    att = db.session.get(Attachment, attachment_id)
    if not att:
        raise api_error(404, "not_found", "Attachment not found")

    snipsel = db.session.get(Snipsel, att.snipsel_id)
    if not snipsel or snipsel.owner_user_id != user.id or snipsel.deleted_at is not None:
        raise api_error(404, "not_found", "Attachment not found")

    path = _resolve_attachment_path(att)
    if not path:
        raise api_error(404, "not_found", "Attachment file missing")

    try:
        return send_file(str(path), as_attachment=True, download_name=att.filename)
    except FileNotFoundError:
        raise api_error(404, "not_found", "Attachment file missing")


@attachments_bp.get("/attachments/<attachment_id>/thumbnail")
@require_auth
def download_thumbnail(attachment_id: str):
    user = current_user()
    att = db.session.get(Attachment, attachment_id)
    if not att or not att.thumbnail_path:
        raise api_error(404, "not_found", "Thumbnail not found")

    snipsel = db.session.get(Snipsel, att.snipsel_id)
    if not snipsel or snipsel.owner_user_id != user.id or snipsel.deleted_at is not None:
        raise api_error(404, "not_found", "Thumbnail not found")

    path = _resolve_thumbnail_path(att)
    if not path:
        raise api_error(404, "not_found", "Thumbnail file missing")

    try:
        return send_file(str(path), as_attachment=False)
    except FileNotFoundError:
        raise api_error(404, "not_found", "Thumbnail file missing")


@attachments_bp.delete("/attachments/<attachment_id>")
@require_auth
def delete_attachment(attachment_id: str):
    user = current_user()
    att = db.session.get(Attachment, attachment_id)
    if not att:
        raise api_error(404, "not_found", "Attachment not found")

    snipsel = db.session.get(Snipsel, att.snipsel_id)
    if not snipsel or snipsel.owner_user_id != user.id or snipsel.deleted_at is not None:
        raise api_error(404, "not_found", "Attachment not found")

    file_path = _resolve_attachment_path(att)
    thumb_path = _resolve_thumbnail_path(att)

    for p in [thumb_path, file_path]:
        if not p:
            continue
        try:
            p.unlink(missing_ok=True)
        except OSError:
            pass

    db.session.delete(att)
    db.session.commit()
    return json_response({"ok": True})


def _resolve_attachment_path(att: Attachment) -> Path | None:
    upload_dir = Path(current_app.config.get("SNIPSEL_UPLOAD_DIR", "./uploads"))
    expected = f"{att.id}_{att.filename}"

    backend_dir = Path(current_app.root_path).resolve().parent

    candidates: list[Path] = []
    if att.storage_path:
        p = Path(att.storage_path)
        if p.is_absolute():
            candidates.append(p)
        else:
            candidates.extend(
                [
                    Path(current_app.instance_path) / p,
                    Path(current_app.root_path) / p,
                    backend_dir / p,
                    Path.cwd() / p,
                ]
            )

    candidates.extend(
        [
            upload_dir / expected,
            Path(current_app.instance_path) / "uploads" / expected,
            Path(current_app.root_path) / "uploads" / expected,
            backend_dir / "uploads" / expected,
            Path(__file__).resolve().parent / "uploads" / expected,
            Path.cwd() / "uploads" / expected,
        ]
    )

    found = _first_existing(candidates)
    if found and att.storage_path != str(found):
        att.storage_path = str(found)
        db.session.commit()
    return found


def _resolve_thumbnail_path(att: Attachment) -> Path | None:
    if not att.thumbnail_path:
        return None

    upload_dir = Path(current_app.config.get("SNIPSEL_UPLOAD_DIR", "./uploads"))
    expected = f"{att.id}_thumb.jpg"

    backend_dir = Path(current_app.root_path).resolve().parent

    candidates: list[Path] = []
    p = Path(att.thumbnail_path)
    if p.is_absolute():
        candidates.append(p)
    else:
        candidates.extend(
            [
                Path(current_app.instance_path) / p,
                Path(current_app.root_path) / p,
                backend_dir / p,
                Path.cwd() / p,
            ]
        )

    candidates.extend(
        [
            upload_dir / expected,
            Path(current_app.instance_path) / "uploads" / expected,
            Path(current_app.root_path) / "uploads" / expected,
            backend_dir / "uploads" / expected,
            Path(__file__).resolve().parent / "uploads" / expected,
            Path.cwd() / "uploads" / expected,
        ]
    )

    found = _first_existing(candidates)
    if found and att.thumbnail_path != str(found):
        att.thumbnail_path = str(found)
        db.session.commit()
    return found


def _first_existing(paths: list[Path]) -> Path | None:
    for p in paths:
        try:
            if p.exists():
                return p
        except OSError:
            continue
    return None


def _write_thumbnail(src: Path, dst: Path) -> None:
    if Image is None:
        return
    with Image.open(src) as im:
        im.thumbnail((512, 512))
        im = im.convert("RGB")
        im.save(dst, format="JPEG", quality=80)
