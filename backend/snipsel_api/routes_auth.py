from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from snipsel_api.auth_session import current_user, enforce_json, json_response, require_auth
from snipsel_api.config import Settings
from snipsel_api.emailer import send_password_reset_email
from snipsel_api.errors import api_error
from snipsel_api.extensions import db
from snipsel_api.models import PasswordResetToken, User

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    enforce_json()
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not username or not email or not password:
        raise api_error(400, "invalid_input", "username, email and password are required")

    existing = db.session.execute(
        db.select(User).where((User.username == username) | (User.email == email))
    ).scalars().first()
    if existing:
        raise api_error(409, "already_exists", "username or email already exists")

    user = User(username=username, email=email, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()

    session.permanent = True
    session["user_id"] = user.id
    return json_response({"user": _user_json(user)}, status=201)


@auth_bp.post("/login")
def login():
    enforce_json()
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        raise api_error(400, "invalid_input", "username and password are required")

    user = db.session.execute(db.select(User).where(User.username == username)).scalars().first()
    if not user or not user.is_active or user.deleted_at is not None:
        raise api_error(401, "invalid_credentials", "Invalid credentials")

    if not check_password_hash(user.password_hash, password):
        raise api_error(401, "invalid_credentials", "Invalid credentials")

    session.permanent = True
    session["user_id"] = user.id
    return json_response({"user": _user_json(user)})


@auth_bp.post("/logout")
def logout():
    session.pop("user_id", None)
    return json_response({"ok": True})


@auth_bp.get("/me")
@require_auth
def me():
    user = current_user()
    return json_response({"user": _user_json(user)})


@auth_bp.patch("/me")
@require_auth
def update_me():
    enforce_json()
    user = current_user()
    data = request.get_json() or {}

    if "default_collection_header_color" in data:
        user.default_collection_header_color = (
            (data.get("default_collection_header_color") or "").strip() or None
        )

    if "carry_over_open_tasks" in data:
        user.carry_over_open_tasks = bool(data.get("carry_over_open_tasks"))

    user.modified_at = datetime.utcnow()
    db.session.commit()
    return json_response({"user": _user_json(user)})


@auth_bp.post("/password-reset/request")
def password_reset_request():
    enforce_json()
    data = request.get_json() or {}
    email = (data.get("email") or "").strip()
    if not email:
        raise api_error(400, "invalid_input", "email is required")

    user = db.session.execute(db.select(User).where(User.email == email)).scalars().first()
    if not user or user.deleted_at is not None or not user.is_active:
        return json_response({"ok": True})

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = datetime.utcnow() + timedelta(hours=2)

    prt = PasswordResetToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at)
    db.session.add(prt)
    db.session.commit()

    settings = Settings.from_env()
    send_password_reset_email(settings=settings, to_email=user.email, token=raw_token)
    return json_response({"ok": True})


@auth_bp.post("/password-reset/confirm")
def password_reset_confirm():
    enforce_json()
    data = request.get_json() or {}
    token = data.get("token") or ""
    new_password = data.get("new_password") or ""
    if not token or not new_password:
        raise api_error(400, "invalid_input", "token and new_password are required")

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    prt = db.session.execute(
        db.select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    ).scalars().first()
    if not prt or prt.used_at is not None or prt.expires_at < datetime.utcnow():
        raise api_error(400, "invalid_token", "Token is invalid or expired")

    user = db.session.get(User, prt.user_id)
    if not user or user.deleted_at is not None or not user.is_active:
        raise api_error(400, "invalid_token", "Token is invalid")

    user.password_hash = generate_password_hash(new_password)
    user.modified_at = datetime.utcnow()
    prt.used_at = datetime.utcnow()
    db.session.commit()

    return json_response({"ok": True})


def _user_json(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "default_collection_header_color": user.default_collection_header_color,
        "carry_over_open_tasks": user.carry_over_open_tasks,
        "created_at": user.created_at.isoformat() + "Z",
    }
