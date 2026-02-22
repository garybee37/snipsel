from __future__ import annotations

from datetime import date, datetime, timedelta

from flask import Blueprint, request

from sqlalchemy.exc import IntegrityError

from snipsel_api.auth_session import current_user, enforce_json, json_response, require_auth
from snipsel_api.errors import api_error
from snipsel_api.extensions import db
from snipsel_api.models import Collection, CollectionSnipsel, Snipsel

collections_bp = Blueprint("collections", __name__)


@collections_bp.get("")
@require_auth
def list_collections():
    user = current_user()
    include_archived = request.args.get("include_archived") == "1"
    q = db.select(Collection).where(Collection.owner_user_id == user.id, Collection.deleted_at.is_(None))
    if not include_archived:
        q = q.where(Collection.archived_at.is_(None))
    q = q.order_by(Collection.list_for_day.desc().nullslast(), Collection.created_at.desc())
    items = db.session.execute(q).scalars().all()
    return json_response({"collections": [_collection_json(c) for c in items]})


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
    c = _get_owned_collection(user.id, collection_id)
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
