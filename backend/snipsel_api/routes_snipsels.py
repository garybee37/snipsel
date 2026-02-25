from __future__ import annotations

from datetime import datetime

from flask import Blueprint, request

from snipsel_api.auth_session import current_user, enforce_json, json_response, require_auth
from snipsel_api.errors import api_error
from snipsel_api.extensions import db
from snipsel_api.permissions import can_read_collection, can_write_collection, can_read_snipsel_via_collections, can_write_snipsel_via_collections
from snipsel_api.models import (
    CollectionSnipsel,
    Collection,
    Mention,
    Snipsel,
    SnipselLink,
    SnipselMention,
    SnipselTag,
    Tag,
    User,
    Notification
)


def _touch_collections_for_snipsel(*, snipsel_id: str, modified_by_id: str) -> None:
    now = datetime.utcnow()
    collection_ids = (
        db.session.execute(
            db.select(CollectionSnipsel.collection_id).where(CollectionSnipsel.snipsel_id == snipsel_id)
        )
        .scalars()
        .all()
    )
    if not collection_ids:
        return
    db.session.execute(
        db.update(Collection)
        .where(Collection.id.in_(collection_ids), Collection.deleted_at.is_(None))
        .values(modified_at=now, modified_by_id=modified_by_id)
    )

from sqlalchemy.orm import joinedload
from snipsel_api.utils_text import extract_mentions, extract_tags

snipsels_bp = Blueprint("snipsels", __name__)


@snipsels_bp.get("/collections/<collection_id>/snipsels")
@require_auth
def list_collection_snipsels(collection_id: str):
    user = current_user()
    if not can_read_collection(user.id, collection_id):
        raise api_error(404, "not_found", "Collection not found")
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
    if not can_write_collection(user.id, collection_id):
        raise api_error(404, "not_found", "Collection not found")
    data = request.get_json() or {}

    snipsel_type = data.get("type")
    if not snipsel_type:
        col = db.session.execute(
            db.select(Collection).where(
                Collection.id == collection_id,
                Collection.owner_user_id == user.id,
                Collection.deleted_at.is_(None),
            )
        ).scalars().first()
        snipsel_type = (col.default_snipsel_type if col and col.default_snipsel_type else "text")
    content_markdown = data.get("content_markdown")

    geo_lat = data.get("geo_lat")
    geo_lng = data.get("geo_lng")
    geo_accuracy_m = data.get("geo_accuracy_m")

    s = Snipsel(
        owner_user_id=user.id,
        type=snipsel_type,
        content_markdown=content_markdown,
        geo_lat=float(geo_lat) if geo_lat is not None else None,
        geo_lng=float(geo_lng) if geo_lng is not None else None,
        geo_accuracy_m=float(geo_accuracy_m) if geo_accuracy_m is not None else None,
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
    if not can_write_collection(user.id, collection_id):
        raise api_error(404, "not_found", "Collection not found")

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
    db.session.execute(
        db.update(Collection)
        .where(Collection.id == collection_id, Collection.deleted_at.is_(None))
        .values(modified_at=datetime.utcnow(), modified_by_id=user.id)
    )
    db.session.commit()
    return json_response({"item": _collection_item_json(cs)}, status=201)


@snipsels_bp.post("/collections/<collection_id>/snipsels/<snipsel_id>/copy")
@require_auth
def copy_snipsel(collection_id: str, snipsel_id: str):
    user = current_user()
    if not can_write_collection(user.id, collection_id):
        raise api_error(404, "not_found", "Collection not found")

    src = db.session.get(Snipsel, snipsel_id)
    if not src or src.deleted_at is not None:
        raise api_error(404, "not_found", "Snipsel not found")
    if src.owner_user_id != user.id and not can_read_snipsel_via_collections(user.id, snipsel_id):
        raise api_error(404, "not_found", "Snipsel not found")

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
    if not s or s.deleted_at is not None:
        raise api_error(404, "not_found", "Snipsel not found")

    can_read = s.owner_user_id == user.id or can_read_snipsel_via_collections(user.id, snipsel_id)
    if not can_read:
        uname = (getattr(user, "username", "") or "").strip().casefold()
        if not uname:
            raise api_error(404, "not_found", "Snipsel not found")
        is_mentioned = (
            db.session.execute(
                db.select(db.func.count())
                .select_from(SnipselMention)
                .join(Mention, Mention.id == SnipselMention.mention_id)
                .where(SnipselMention.snipsel_id == snipsel_id, Mention.name == uname)
            ).scalar()
            or 0
        )
        if is_mentioned <= 0:
            raise api_error(404, "not_found", "Snipsel not found")

    has_collection_access = s.owner_user_id == user.id or can_read_snipsel_via_collections(user.id, snipsel_id)
    has_write_access = s.owner_user_id == user.id or can_write_snipsel_via_collections(user.id, snipsel_id)
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

    tag_names = (
        db.session.execute(
            db.select(Tag.name)
            .join(SnipselTag, SnipselTag.tag_id == Tag.id)
            .where(Tag.owner_user_id == user.id, SnipselTag.snipsel_id == snipsel_id)
            .order_by(Tag.name.asc())
        )
        .scalars()
        .all()
    )

    mention_names = (
        db.session.execute(
            db.select(Mention.name)
            .join(SnipselMention, SnipselMention.mention_id == Mention.id)
            .where(Mention.owner_user_id == user.id, SnipselMention.snipsel_id == snipsel_id)
            .order_by(Mention.name.asc())
        )
        .scalars()
        .all()
    )

    can_toggle_task_done = bool(s.type == "task" and (has_collection_access or is_mentioned))

    return json_response(
        {
            "snipsel": _snipsel_json(s),
            "has_collection_access": bool(has_collection_access),
            "has_write_access": bool(has_write_access),
            "can_toggle_task_done": bool(can_toggle_task_done),
            "tags": [n for n in tag_names if n and n[:1].isalpha()],
            "mentions": [n for n in mention_names if n and n[:1].isalpha()],
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
    s = db.session.get(Snipsel, snipsel_id)
    if not s or s.deleted_at is not None:
        raise api_error(404, "not_found", "Snipsel not found")
    has_collection_access = s.owner_user_id == user.id or can_read_snipsel_via_collections(user.id, snipsel_id)
    has_write_access = s.owner_user_id == user.id or can_write_snipsel_via_collections(user.id, snipsel_id)

    uname = (getattr(user, "username", "") or "").strip().casefold()
    is_mentioned = False
    if uname:
        is_mentioned = (
            (db.session.execute(
                db.select(db.func.count())
                .select_from(SnipselMention)
                .join(Mention, Mention.id == SnipselMention.mention_id)
                .where(SnipselMention.snipsel_id == snipsel_id, Mention.name == uname)
            ).scalar() or 0)
            > 0
        )

    can_toggle_task_done = bool(
        s.type == "task" and (has_collection_access or is_mentioned)
    )

    if not has_write_access:
        if not (can_toggle_task_done and "task_done" in (request.get_json() or {})):
            raise api_error(404, "not_found", "Snipsel not found")
    data = request.get_json() or {}

    old_type = s.type
    if "type" in data and has_write_access:
        new_type = data.get("type")
        if isinstance(new_type, str) and new_type:
            s.type = new_type
    if "content_markdown" in data and has_write_access:
        s.content_markdown = data.get("content_markdown")
    if "task_done" in data:
        done = bool(data.get("task_done"))
        old_done = s.task_done
        s.task_done = done
        if done:
            s.done_at = datetime.utcnow()
            s.done_by_id = user.id
            if not old_done and user.id != s.created_by_id and s.created_by_id:
                n = Notification(
                    user_id=s.created_by_id,
                    message=f"{user.username} completed a task you created.",
                    snipsel_id=s.id
                )
                db.session.add(n)
        else:
            s.done_at = None
            s.done_by_id = None
    if "external_url" in data and has_write_access:
        s.external_url = data.get("external_url")
    if "external_label" in data and has_write_access:
        s.external_label = data.get("external_label")
    if "internal_target_snipsel_id" in data and has_write_access:
        s.internal_target_snipsel_id = data.get("internal_target_snipsel_id")

    s.modified_by_id = user.id
    if has_write_access:
        _sync_tags_mentions(user_id=s.owner_user_id, snipsel=s, newly_became_task=(old_type != "task" and s.type == "task"))
    _touch_collections_for_snipsel(snipsel_id=snipsel_id, modified_by_id=user.id)
    db.session.commit()
    return json_response({"snipsel": _snipsel_json(s)})


@snipsels_bp.delete("/collections/<collection_id>/snipsels/<snipsel_id>")
@require_auth
def delete_from_collection(collection_id: str, snipsel_id: str):
    user = current_user()
    if not can_write_collection(user.id, collection_id):
        raise api_error(404, "not_found", "Collection not found")

    s = db.session.get(Snipsel, snipsel_id)
    if not s or s.deleted_at is not None:
        raise api_error(404, "not_found", "Snipsel not found")
    if s.owner_user_id != user.id and not can_read_snipsel_via_collections(user.id, snipsel_id):
        raise api_error(404, "not_found", "Snipsel not found")

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
    if remaining == 0 and s.owner_user_id == user.id:
        if s.deleted_at is None:
            s.deleted_at = datetime.utcnow()
            s.deleted_by_id = user.id

    db.session.execute(
        db.update(Collection)
        .where(Collection.id == collection_id, Collection.deleted_at.is_(None))
        .values(modified_at=datetime.utcnow(), modified_by_id=user.id)
    )
    db.session.commit()
    return json_response({"ok": True})


@snipsels_bp.patch("/collections/<collection_id>/snipsels/reorder")
@require_auth
def reorder_collection(collection_id: str):
    enforce_json()
    user = current_user()
    if not can_write_collection(user.id, collection_id):
        raise api_error(404, "not_found", "Collection not found")
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

        s = db.session.get(Snipsel, snipsel_id)
        if not s or s.deleted_at is not None:
            continue
        if s.owner_user_id != user.id and not can_read_snipsel_via_collections(user.id, snipsel_id):
            continue

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

    db.session.execute(
        db.update(Collection)
        .where(Collection.id == collection_id, Collection.deleted_at.is_(None))
        .values(modified_at=datetime.utcnow(), modified_by_id=user.id)
    )
    db.session.commit()
    return json_response({"ok": True})


def _get_owned_snipsel(user_id: str, snipsel_id: str) -> Snipsel:
    s = db.session.get(Snipsel, snipsel_id)
    if not s or s.deleted_at is not None or s.owner_user_id != user_id:
        raise api_error(404, "not_found", "Snipsel not found")
    return s


def _sync_tags_mentions(*, user_id: str, snipsel: Snipsel, newly_became_task: bool = False) -> None:
    text = snipsel.content_markdown or ""
    tag_names = extract_tags(text)
    mention_names = extract_mentions(text)

    old_mention_names = set(db.session.execute(
        db.select(Mention.name).join(SnipselMention, SnipselMention.mention_id == Mention.id)
        .where(SnipselMention.snipsel_id == snipsel.id)
    ).scalars().all())
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

    for name in set(mention_names):
        if name not in old_mention_names or newly_became_task:
            mentioned_user = db.session.execute(db.select(User).where(User.username == name)).scalar_one_or_none()
            if mentioned_user and mentioned_user.id != user_id:
                if snipsel.type == "task" or can_read_snipsel_via_collections(mentioned_user.id, snipsel.id):
                    author = db.session.get(User, user_id)
                    author_name = author.username if author else "Someone"
                    msg = f"{author_name} assigned a task to you." if snipsel.type == "task" else f"{author_name} mentioned you in a snipsel."
                    n = Notification(
                        user_id=mentioned_user.id,
                        message=msg,
                        snipsel_id=snipsel.id
                    )
                    db.session.add(n)
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
        "geo_lat": s.geo_lat,
        "geo_lng": s.geo_lng,
        "geo_accuracy_m": s.geo_accuracy_m,
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
