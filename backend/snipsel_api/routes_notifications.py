from __future__ import annotations

from flask import Blueprint, request
from snipsel_api.auth_session import (
    current_user,
    enforce_json,
    json_response,
    require_auth,
)
from snipsel_api.extensions import db
from snipsel_api.models import Notification

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.get("")
@require_auth
def list_notifications():
    user = current_user()
    
    from snipsel_api.reminders import process_reminders
    process_reminders(user.id)

    q = (
        db.select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
    )

    items = db.session.execute(q).scalars().all()

    out = []
    for n in items:
        out.append(
            {
                "id": n.id,
                "message": n.message,
                "is_read": n.is_read,
                "snipsel_id": n.snipsel_id,
                "collection_id": n.collection_id,
                "created_at": n.created_at.isoformat() + "Z",
            }
        )

    return json_response({"notifications": out})


@notifications_bp.post("/<id>/mark-read")
@require_auth
def mark_read(id: str):
    user = current_user()
    n = db.session.execute(
        db.select(Notification).where(
            Notification.id == id, Notification.user_id == user.id
        )
    ).scalar_one_or_none()

    if n:
        n.is_read = True
        db.session.commit()

    return json_response({"success": True})


@notifications_bp.post("/mark-all-read")
@require_auth
def mark_all_read():
    user = current_user()
    notifications = (
        db.session.execute(
            db.select(Notification).where(
                Notification.user_id == user.id, Notification.is_read == False
            )
        )
        .scalars()
        .all()
    )

    for n in notifications:
        n.is_read = True

    db.session.commit()
    return json_response({"success": True})


@notifications_bp.delete("/read")
@require_auth
def delete_read_notifications():
    user = current_user()
    
    db.session.execute(
        db.delete(Notification).where(
            Notification.user_id == user.id,
            Notification.is_read == True
        )
    )
    
    db.session.commit()
    return json_response({"success": True})
