from __future__ import annotations

from datetime import datetime

from flask import Blueprint, request

from snipsel_api.auth_session import current_user, enforce_json, json_response, require_auth
from snipsel_api.errors import api_error
from snipsel_api.extensions import db
from snipsel_api.models import (
    CollectionSnipsel,
    Collection,
    Mention,
    Snipsel,
    SnipselLink,
    SnipselMention,
    SnipselTag,
    Tag,
)

from sqlalchemy.orm import joinedload
from snipsel_api.utils_text import extract_mentions, extract_tags

snipsels_bp = Blueprint("snipsels", __name__)


@snipsels_bp.get("/collections/<collection_id>/snipsels")
@require_auth
def list_collection_snipsels(collection_id: str):
    user = current_user()
    items = (
        db.session.execute(
            db.select(CollectionSnipsel)
            .join(Snipsel, Snipsel.id == CollectionSnipsel.snipsel_id)
            .options(
                joinedload(CollectionSnipsel.snipsel).joinedload(Snipsel.created_by),
                joinedload(CollectionSnipsel.snipsel).joinedload(Snipsel.modified_by),
                joinedload(CollectionSnipsel.snipsel).joinedload(Snipsel.done_by),
            )
            .where(
                CollectionSnipsel.collection_id == collection_id,
                Snipsel.owner_user_id == user.id,
                Snipsel.deleted_at.is_(None),
            )
            .order_by(CollectionSnipsel.position.asc())
        )
        .scalars()
        .all()
    )
    return json_response({"items": [_collection_item_json(cs) for cs in items]})


@snipsels_bp.post("/collections/<collection_id>/snipsels")
@require_auth
def create_snipsel(collection_id: str):
    enforce_json()
    user = current_user()
    data = request.get_json() or {}

    snipsel_type = data.get("type") or "text"
    content_markdown = data.get("content_markdown")

    s = Snipsel(
        owner_user_id=user.id,
        type=snipsel_type,
        content_markdown=content_markdown,
        created_by_id=user.id,
        modified_by_id=user.id,
    )
    db.session.add(s)
    db.session.flush()

    max_pos = (
        db.session.execute(
            db.select(db.func.max(CollectionSnipsel.position)).where(CollectionSnipsel.collection_id == collection_id)
        ).scalar()
        or 0
    )
    cs = CollectionSnipsel(collection_id=collection_id, snipsel_id=s.id, position=max_pos + 1, indent=0)
    db.session.add(cs)

    _sync_tags_mentions(user_id=user.id, snipsel=s)
    _sync_backlinks(user_id=user.id, snipsel=s)
    db.session.commit()

    return json_response({"item": _collection_item_json(cs)}, status=201)


@snipsels_bp.post("/collections/<collection_id>/snipsels/<snipsel_id>/reference")
@require_auth
def reference_snipsel(collection_id: str, snipsel_id: str):
    user = current_user()
    s = _get_owned_snipsel(user.id, snipsel_id)

    exists = db.session.execute(
        db.select(CollectionSnipsel).where(
            CollectionSnipsel.collection_id == collection_id,
            CollectionSnipsel.snipsel_id == snipsel_id,
        )
    ).scalars().first()
    if exists:
        return json_response({"item": _collection_item_json(exists)})

    max_pos = (
        db.session.execute(
            db.select(db.func.max(CollectionSnipsel.position)).where(CollectionSnipsel.collection_id == collection_id)
        ).scalar()
        or 0
    )
    cs = CollectionSnipsel(collection_id=collection_id, snipsel_id=s.id, position=max_pos + 1, indent=0)
    db.session.add(cs)
    db.session.commit()
    return json_response({"item": _collection_item_json(cs)}, status=201)


@snipsels_bp.post("/collections/<collection_id>/snipsels/<snipsel_id>/copy")
@require_auth
def copy_snipsel(collection_id: str, snipsel_id: str):
    user = current_user()
    src = _get_owned_snipsel(user.id, snipsel_id)

    s = Snipsel(
        owner_user_id=user.id,
        type=src.type,
        content_markdown=src.content_markdown,
        task_done=src.task_done,
        done_at=src.done_at,
        done_by_id=src.done_by_id,
        external_url=src.external_url,
        external_label=src.external_label,
        internal_target_snipsel_id=src.internal_target_snipsel_id,
        created_by_id=user.id,
        modified_by_id=user.id,
    )
    db.session.add(s)
    db.session.flush()

    max_pos = (
        db.session.execute(
            db.select(db.func.max(CollectionSnipsel.position)).where(CollectionSnipsel.collection_id == collection_id)
        ).scalar()
        or 0
    )
    cs = CollectionSnipsel(collection_id=collection_id, snipsel_id=s.id, position=max_pos + 1, indent=0)
    db.session.add(cs)
    _sync_tags_mentions(user_id=user.id, snipsel=s)
    _sync_backlinks(user_id=user.id, snipsel=s)
    db.session.commit()
    return json_response({"item": _collection_item_json(cs)}, status=201)


@snipsels_bp.get("/snipsels/<snipsel_id>")
@require_auth
def get_snipsel(snipsel_id: str):
    user = current_user()
    s = (
        db.session.execute(
            db.select(Snipsel)
            .options(joinedload(Snipsel.created_by), joinedload(Snipsel.modified_by), joinedload(Snipsel.done_by))
            .where(Snipsel.id == snipsel_id)
        )
        .scalars()
        .first()
    )
    if not s or s.deleted_at is not None or s.owner_user_id != user.id:
        raise api_error(404, "not_found", "Snipsel not found")
    placements = (
        db.session.execute(
            db.select(CollectionSnipsel)
            .join(Collection, Collection.id == CollectionSnipsel.collection_id)
            .where(
                CollectionSnipsel.snipsel_id == snipsel_id,
                Collection.owner_user_id == user.id,
                Collection.deleted_at.is_(None),
            )
        )
        .scalars()
        .all()
    )

    backlinks = (
        db.session.execute(
            db.select(SnipselLink).where(SnipselLink.to_snipsel_id == snipsel_id)
        )
        .scalars()
        .all()
    )

    return json_response(
        {
            "snipsel": _snipsel_json(s),
            "placements": [
                {
                    "collection_id": cs.collection_id,
                    "collection_title": cs.collection.title,
                    "collection_icon": cs.collection.icon,
                    "position": cs.position,
                    "indent": cs.indent,
                }
                for cs in placements
            ],
            "backlinks": [
                {
                    "from_snipsel_id": l.from_snipsel_id,
                    "to_snipsel_id": l.to_snipsel_id,
                }
                for l in backlinks
            ],
        }
    )


@snipsels_bp.patch("/snipsels/<snipsel_id>")
@require_auth
def update_snipsel(snipsel_id: str):
    enforce_json()
    user = current_user()
    s = _get_owned_snipsel(user.id, snipsel_id)
    data = request.get_json() or {}

    if "type" in data:
        new_type = data.get("type")
        if isinstance(new_type, str) and new_type:
            s.type = new_type
    if "content_markdown" in data:
        s.content_markdown = data.get("content_markdown")
    if "task_done" in data:
        done = bool(data.get("task_done"))
        s.task_done = done
        if done:
            s.done_at = datetime.utcnow()
            s.done_by_id = user.id
        else:
            s.done_at = None
            s.done_by_id = None
    if "external_url" in data:
        s.external_url = data.get("external_url")
    if "external_label" in data:
        s.external_label = data.get("external_label")
    if "internal_target_snipsel_id" in data:
        s.internal_target_snipsel_id = data.get("internal_target_snipsel_id")

    s.modified_by_id = user.id
    _sync_tags_mentions(user_id=user.id, snipsel=s)
    _sync_backlinks(user_id=user.id, snipsel=s)
    db.session.commit()
    return json_response({"snipsel": _snipsel_json(s)})


@snipsels_bp.delete("/collections/<collection_id>/snipsels/<snipsel_id>")
@require_auth
def delete_from_collection(collection_id: str, snipsel_id: str):
    user = current_user()
    _get_owned_snipsel(user.id, snipsel_id)

    cs = db.session.execute(
        db.select(CollectionSnipsel).where(
            CollectionSnipsel.collection_id == collection_id,
            CollectionSnipsel.snipsel_id == snipsel_id,
        )
    ).scalars().first()
    if not cs:
        raise api_error(404, "not_found", "Snipsel not in collection")

    db.session.delete(cs)

    remaining = (
        db.session.execute(db.select(db.func.count()).select_from(CollectionSnipsel).where(CollectionSnipsel.snipsel_id == snipsel_id)).scalar()
        or 0
    )
    if remaining <= 1:
        s = db.session.get(Snipsel, snipsel_id)
        if s and s.deleted_at is None:
            s.deleted_at = datetime.utcnow()
            s.deleted_by_id = user.id

    db.session.commit()
    return json_response({"ok": True})


@snipsels_bp.patch("/collections/<collection_id>/snipsels/reorder")
@require_auth
def reorder_collection(collection_id: str):
    enforce_json()
    user = current_user()
    data = request.get_json() or {}
    items = data.get("items")
    if not isinstance(items, list):
        raise api_error(400, "invalid_input", "items must be a list")

    for item in items:
        if not isinstance(item, dict):
            continue
        snipsel_id = item.get("snipsel_id")
        position = item.get("position")
        indent = item.get("indent")
        if not snipsel_id:
            continue

        _get_owned_snipsel(user.id, snipsel_id)

        cs = db.session.execute(
            db.select(CollectionSnipsel).where(
                CollectionSnipsel.collection_id == collection_id,
                CollectionSnipsel.snipsel_id == snipsel_id,
            )
        ).scalars().first()
        if not cs:
            continue

        if isinstance(position, int):
            cs.position = position
        if isinstance(indent, int) and indent >= 0:
            cs.indent = indent

    db.session.commit()
    return json_response({"ok": True})


def _get_owned_snipsel(user_id: str, snipsel_id: str) -> Snipsel:
    s = db.session.get(Snipsel, snipsel_id)
    if not s or s.deleted_at is not None or s.owner_user_id != user_id:
        raise api_error(404, "not_found", "Snipsel not found")
    return s


def _sync_tags_mentions(*, user_id: str, snipsel: Snipsel) -> None:
    text = snipsel.content_markdown or ""
    tag_names = extract_tags(text)
    mention_names = extract_mentions(text)

    existing_tags = (
        db.session.execute(
            db.select(Tag).where(Tag.owner_user_id == user_id, Tag.name.in_(tag_names))
        ).scalars().all()
        if tag_names
        else []
    )
    by_name = {t.name: t for t in existing_tags}
    for name in tag_names:
        if name not in by_name:
            t = Tag(owner_user_id=user_id, name=name)
            db.session.add(t)
            db.session.flush()
            by_name[name] = t

    db.session.execute(db.delete(SnipselTag).where(SnipselTag.snipsel_id == snipsel.id))
    for t in by_name.values():
        db.session.add(SnipselTag(snipsel_id=snipsel.id, tag_id=t.id))

    existing_mentions = (
        db.session.execute(
            db.select(Mention).where(Mention.owner_user_id == user_id, Mention.name.in_(mention_names))
        ).scalars().all()
        if mention_names
        else []
    )
    m_by_name = {m.name: m for m in existing_mentions}
    for name in mention_names:
        if name not in m_by_name:
            m = Mention(owner_user_id=user_id, name=name)
            db.session.add(m)
            db.session.flush()
            m_by_name[name] = m

    db.session.execute(db.delete(SnipselMention).where(SnipselMention.snipsel_id == snipsel.id))
    for m in m_by_name.values():
        db.session.add(SnipselMention(snipsel_id=snipsel.id, mention_id=m.id))


def _sync_backlinks(*, user_id: str, snipsel: Snipsel) -> None:
    db.session.execute(db.delete(SnipselLink).where(SnipselLink.from_snipsel_id == snipsel.id))

    target_id = snipsel.internal_target_snipsel_id
    if not target_id:
        return

    target = db.session.get(Snipsel, target_id)
    if not target or target.owner_user_id != user_id or target.deleted_at is not None:
        return

    db.session.add(SnipselLink(from_snipsel_id=snipsel.id, to_snipsel_id=target_id))


def _snipsel_json(s: Snipsel) -> dict:
    return {
        "id": s.id,
        "type": s.type,
        "content_markdown": s.content_markdown,
        "task_done": s.task_done,
        "done_at": s.done_at.isoformat() + "Z" if s.done_at else None,
        "done_by_id": s.done_by_id,
        "done_by_username": s.done_by.username if s.done_by else None,
        "external_url": s.external_url,
        "external_label": s.external_label,
        "internal_target_snipsel_id": s.internal_target_snipsel_id,
        "created_at": s.created_at.isoformat() + "Z",
        "created_by_id": s.created_by_id,
        "created_by_username": s.created_by.username if s.created_by else None,
        "modified_at": s.modified_at.isoformat() + "Z",
        "modified_by_id": s.modified_by_id,
        "modified_by_username": s.modified_by.username if s.modified_by else None,
        "attachments": [
            {
                "id": a.id,
                "filename": a.filename,
                "mime_type": a.mime_type,
                "size_bytes": a.size_bytes,
                "has_thumbnail": a.thumbnail_path is not None,
            }
            for a in s.attachments
        ],
    }


def _collection_item_json(cs: CollectionSnipsel) -> dict:
    return {
        "collection_id": cs.collection_id,
        "snipsel_id": cs.snipsel_id,
        "position": cs.position,
        "indent": cs.indent,
        "snipsel": _snipsel_json(cs.snipsel),
    }
