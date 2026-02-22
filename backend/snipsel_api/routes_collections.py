from __future__ import annotations

from datetime import date, datetime, timedelta

from flask import Blueprint, request

from sqlalchemy.exc import IntegrityError

from snipsel_api.auth_session import current_user, enforce_json, json_response, require_auth
from snipsel_api.errors import api_error
from snipsel_api.extensions import db
from snipsel_api.models import Collection, CollectionShare, CollectionSnipsel, Snipsel, User
from snipsel_api.permissions import can_read_collection, can_write_collection, get_collection_access_level

collections_bp = Blueprint("collections", __name__)


def _get_share_permission(user_id: str, collection_id: str) -> str | None:
    level = get_collection_access_level(user_id, collection_id)
    if level in {"owner", "write", "read"}:
        return "write" if level == "write" else ("read" if level == "read" else None)
    return None


@collections_bp.get("")
@require_auth
def list_collections():
    user = current_user()
    include_archived = request.args.get("include_archived") == "1"
    owned = db.select(Collection).where(Collection.owner_user_id == user.id, Collection.deleted_at.is_(None))
    if not include_archived:
        owned = owned.where(Collection.archived_at.is_(None))

    shared = (
        db.select(Collection)
        .join(CollectionShare, CollectionShare.collection_id == Collection.id)
        .where(
            Collection.deleted_at.is_(None),
            CollectionShare.shared_with_user_id == user.id,
        )
    )
    if not include_archived:
        shared = shared.where(Collection.archived_at.is_(None))

    items = db.session.execute(owned.union(shared).order_by(Collection.list_for_day.desc().nullslast(), Collection.created_at.desc())).scalars().all()

    out = []
    for c in items:
        j = _collection_json(c)
        level = get_collection_access_level(user.id, c.id)
        j["access_level"] = level or "read"
        if c.owner_user_id != user.id:
            j["shared_by_username"] = (
                db.session.execute(db.select(User.username).where(User.id == c.owner_user_id)).scalars().first()
            )
        out.append(j)

    return json_response({"collections": out})


@collections_bp.get("/today")
@require_auth
def get_today_collection():
    user = current_user()
    day_str = request.args.get("day")
    day = date.fromisoformat(day_str) if day_str else date.today()

    existing = db.session.execute(
        db.select(Collection).where(
            Collection.owner_user_id == user.id,
            Collection.list_for_day == day,
            Collection.deleted_at.is_(None),
        )
    ).scalars().first()
    if existing:
        _maybe_carry_over_open_tasks(user=user, today_collection=existing, day=day)
        return json_response({"collection": _collection_json(existing)})

    conflict_deleted = db.session.execute(
        db.select(Collection).where(
            Collection.owner_user_id == user.id,
            Collection.list_for_day == day,
            Collection.deleted_at.is_not(None),
        )
    ).scalars().first()
    if conflict_deleted:
        conflict_deleted.list_for_day = None
        db.session.commit()

    c = Collection(
        owner_user_id=user.id,
        title=day.isoformat(),
        icon="📅",
        list_for_day=day,
        header_color=user.default_collection_header_color,
        created_by_id=user.id,
        modified_by_id=user.id,
    )
    db.session.add(c)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise api_error(409, "conflict", "Day collection could not be created")

    _maybe_carry_over_open_tasks(user=user, today_collection=c, day=day)
    return json_response({"collection": _collection_json(c)}, status=201)


def _maybe_carry_over_open_tasks(user, today_collection: Collection, day: date) -> None:
    if day != date.today():
        return
    if not getattr(user, "carry_over_open_tasks", True):
        return

    start_day = day - timedelta(days=30)

    past_collections = (
        db.session.execute(
            db.select(Collection)
            .where(
                Collection.owner_user_id == user.id,
                Collection.deleted_at.is_(None),
                Collection.list_for_day.is_not(None),
                Collection.list_for_day >= start_day,
                Collection.list_for_day < day,
            )
            .order_by(Collection.list_for_day.desc())
        )
        .scalars()
        .all()
    )

    if not past_collections:
        return

    max_pos = (
        db.session.execute(
            db.select(db.func.max(CollectionSnipsel.position)).where(
                CollectionSnipsel.collection_id == today_collection.id
            )
        ).scalar()
        or 0
    )

    for src in past_collections:
        items = (
            db.session.execute(
                db.select(CollectionSnipsel)
                .join(Snipsel, Snipsel.id == CollectionSnipsel.snipsel_id)
                .where(
                    CollectionSnipsel.collection_id == src.id,
                    Snipsel.owner_user_id == user.id,
                    Snipsel.deleted_at.is_(None),
                    Snipsel.type == "task",
                    Snipsel.task_done == False,
                )
                .order_by(CollectionSnipsel.position.asc())
            )
            .scalars()
            .all()
        )

        for cs in items:
            already = db.session.execute(
                db.select(CollectionSnipsel).where(
                    CollectionSnipsel.collection_id == today_collection.id,
                    CollectionSnipsel.snipsel_id == cs.snipsel_id,
                )
            ).scalars().first()
            if already:
                db.session.delete(cs)
                continue

            max_pos += 1
            cs.collection_id = today_collection.id
            cs.position = max_pos
            cs.indent = 0

    db.session.commit()


@collections_bp.post("")
@require_auth
def create_collection():
    enforce_json()
    user = current_user()
    data = request.get_json() or {}

    title = (data.get("title") or "").strip()
    icon = (data.get("icon") or "🗒").strip() or "🗒"
    header_image_url = (data.get("header_image_url") or "").strip() or None
    header_color = (data.get("header_color") or "").strip() or user.default_collection_header_color or None
    is_favorite = bool(data.get("is_favorite"))
    default_snipsel_type = (data.get("default_snipsel_type") or "").strip() or None

    if not title:
        raise api_error(400, "invalid_input", "title is required")

    c = Collection(
        owner_user_id=user.id,
        title=title,
        icon=icon,
        header_image_url=header_image_url,
        header_color=header_color,
        is_favorite=is_favorite,
        default_snipsel_type=default_snipsel_type,
        created_by_id=user.id,
        modified_by_id=user.id,
    )
    db.session.add(c)
    db.session.commit()
    return json_response({"collection": _collection_json(c)}, status=201)


@collections_bp.get("/<collection_id>")
@require_auth
def get_collection(collection_id: str):
    user = current_user()
    if not can_read_collection(user.id, collection_id):
        raise api_error(404, "not_found", "Collection not found")
    c = db.session.get(Collection, collection_id)
    if not c or c.deleted_at is not None:
        raise api_error(404, "not_found", "Collection not found")
    return json_response({"collection": _collection_json(c)})


@collections_bp.patch("/<collection_id>")
@require_auth
def update_collection(collection_id: str):
    enforce_json()
    user = current_user()
    c = _get_owned_collection(user.id, collection_id)
    data = request.get_json() or {}

    if "title" in data:
        title = (data.get("title") or "").strip()
        if not title:
            raise api_error(400, "invalid_input", "title cannot be empty")
        c.title = title
    if "icon" in data:
        icon = (data.get("icon") or "").strip()
        if not icon:
            raise api_error(400, "invalid_input", "icon cannot be empty")
        c.icon = icon
    if "header_image_url" in data:
        c.header_image_url = (data.get("header_image_url") or "").strip() or None
    if "header_color" in data:
        c.header_color = (data.get("header_color") or "").strip() or None
    if "archived" in data:
        archived = bool(data.get("archived"))
        c.archived_at = datetime.utcnow() if archived else None
    if "is_favorite" in data:
        c.is_favorite = bool(data.get("is_favorite"))
    if "default_snipsel_type" in data:
        c.default_snipsel_type = (data.get("default_snipsel_type") or "").strip() or None

    c.modified_by_id = user.id
    db.session.commit()
    return json_response({"collection": _collection_json(c)})


@collections_bp.delete("/<collection_id>")
@require_auth
def delete_collection(collection_id: str):
    user = current_user()
    c = _get_owned_collection(user.id, collection_id)
    c.deleted_at = datetime.utcnow()
    c.deleted_by_id = user.id
    if c.list_for_day is not None:
        c.list_for_day = None
    db.session.commit()
    return json_response({"ok": True})


def _get_owned_collection(user_id: str, collection_id: str) -> Collection:
    c = db.session.get(Collection, collection_id)
    if not c or c.deleted_at is not None or c.owner_user_id != user_id:
        raise api_error(404, "not_found", "Collection not found")
    return c


def _collection_json(c: Collection) -> dict:
    return {
        "id": c.id,
        "title": c.title,
        "icon": c.icon,
        "header_image_url": c.header_image_url,
        "header_color": c.header_color,
        "is_favorite": c.is_favorite,
        "default_snipsel_type": c.default_snipsel_type,
        "archived": c.archived_at is not None,
        "list_for_day": c.list_for_day.isoformat() if c.list_for_day else None,
        "created_at": c.created_at.isoformat() + "Z",
        "modified_at": c.modified_at.isoformat() + "Z",
    }


@collections_bp.get("/<collection_id>/shares")
@require_auth
def list_shares(collection_id: str):
    user = current_user()
    c = _get_owned_collection(user.id, collection_id)
    _ = c
    rows = (
        db.session.execute(
            db.select(CollectionShare)
            .where(CollectionShare.collection_id == collection_id)
            .order_by(CollectionShare.created_at.asc())
        )
        .scalars()
        .all()
    )
    user_ids = [r.shared_with_user_id for r in rows]
    users_by_id = {
        u.id: u.username
        for u in (
            db.session.execute(db.select(User).where(User.id.in_(user_ids))).scalars().all()
            if user_ids
            else []
        )
    }
    return json_response(
        {
            "shares": [
                {
                    "id": r.id,
                    "shared_with_user_id": r.shared_with_user_id,
                    "shared_with_username": users_by_id.get(r.shared_with_user_id),
                    "permission": r.permission,
                    "created_at": r.created_at.isoformat() + "Z",
                }
                for r in rows
            ]
        }
    )


@collections_bp.post("/<collection_id>/shares")
@require_auth
def create_share(collection_id: str):
    enforce_json()
    user = current_user()
    c = _get_owned_collection(user.id, collection_id)
    data = request.get_json() or {}

    shared_with_user_id = (data.get("shared_with_user_id") or "").strip()
    permission = (data.get("permission") or "").strip()
    if permission not in {"read", "write"}:
        raise api_error(400, "invalid_input", "permission must be read or write")
    if not shared_with_user_id:
        raise api_error(400, "invalid_input", "shared_with_user_id is required")
    if shared_with_user_id == c.owner_user_id:
        raise api_error(400, "invalid_input", "cannot share with owner")

    target = db.session.get(User, shared_with_user_id)
    if not target or target.deleted_at is not None or not target.is_active:
        raise api_error(400, "invalid_input", "user not found")

    existing = db.session.execute(
        db.select(CollectionShare).where(
            CollectionShare.collection_id == collection_id,
            CollectionShare.shared_with_user_id == shared_with_user_id,
        )
    ).scalars().first()
    if existing:
        existing.permission = permission
        db.session.commit()
        return json_response({"share": {"id": existing.id}})

    s = CollectionShare(
        collection_id=collection_id,
        shared_with_user_id=shared_with_user_id,
        permission=permission,
        created_by_user_id=user.id,
    )
    db.session.add(s)
    db.session.commit()
    return json_response({"share": {"id": s.id}}, status=201)


@collections_bp.delete("/<collection_id>/shares/<share_id>")
@require_auth
def delete_share(collection_id: str, share_id: str):
    user = current_user()
    _get_owned_collection(user.id, collection_id)
    s = db.session.get(CollectionShare, share_id)
    if not s or s.collection_id != collection_id:
        raise api_error(404, "not_found", "Share not found")
    db.session.delete(s)
    db.session.commit()
    return json_response({"ok": True})
