from __future__ import annotations

import os
from pathlib import Path

from datetime import timedelta

from flask import Flask

from snipsel_api.config import Settings
from snipsel_api.extensions import cors, db, migrate
from snipsel_api.routes_errors import errors_bp
from snipsel_api.routes_attachments import attachments_bp
from snipsel_api.routes_auth import auth_bp
from snipsel_api.routes_collections import collections_bp
from snipsel_api.routes_search import search_bp
from snipsel_api.routes_snipsels import snipsels_bp
from snipsel_api.routes_users import users_bp
from snipsel_api.routes_notifications import notifications_bp
from snipsel_api.routes_importer import importer_bp
from snipsel_api.routes_proxy import proxy_bp


def create_app() -> Flask:
    settings = Settings.from_env()

    app = Flask(__name__, instance_relative_config=True)
    app.config.update(
        SECRET_KEY=settings.secret_key,
        SQLALCHEMY_DATABASE_URI=settings.database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=settings.max_upload_bytes,
        PERMANENT_SESSION_LIFETIME=timedelta(days=30),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE=settings.session_cookie_samesite,
        SESSION_COOKIE_SECURE=settings.session_cookie_secure,
    )
    upload_dir = settings.upload_dir
    if "SNIPSEL_UPLOAD_DIR" not in os.environ:
        upload_dir = str(Path(app.instance_path) / "uploads")
    app.config["SNIPSEL_UPLOAD_DIR"] = str(Path(upload_dir).expanduser().resolve())

    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": settings.cors_origins}},
        supports_credentials=True,
    )


    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(collections_bp, url_prefix="/api/collections")
    app.register_blueprint(snipsels_bp, url_prefix="/api")
    app.register_blueprint(search_bp, url_prefix="/api")
    app.register_blueprint(users_bp, url_prefix="/api")
    app.register_blueprint(attachments_bp, url_prefix="/api")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")
    app.register_blueprint(importer_bp, url_prefix="/api/importer")
    app.register_blueprint(proxy_bp, url_prefix="/api/proxy")
    app.register_blueprint(errors_bp)

    from snipsel_api import models
    from snipsel_api.commands import cleanup, db_init, process_reminders_command as process_reminders

    app.cli.add_command(cleanup)
    app.cli.add_command(db_init)
    app.cli.add_command(process_reminders)

    _ = models

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
