from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    secret_key: str
    database_url: str
    upload_dir: str
    max_upload_bytes: int
    session_cookie_samesite: str
    session_cookie_secure: bool
    cors_origins: list[str]
    smtp_host: str | None
    smtp_port: int
    smtp_username: str | None
    smtp_password: str | None
    smtp_use_tls: bool
    mail_from: str | None
    public_base_url: str | None
    vapid_private_key: str | None
    vapid_public_key: str | None
    vapid_subject: str | None

    @staticmethod
    def from_env() -> "Settings":
        secret_key = os.environ.get("SNIPSEL_SECRET_KEY", "dev")
        database_url = os.environ.get("SNIPSEL_DATABASE_URL", "sqlite:///snipsel.db")
        upload_dir = os.environ.get("SNIPSEL_UPLOAD_DIR", "./uploads")
        max_upload_bytes = int(os.environ.get("SNIPSEL_MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))

        session_cookie_samesite = os.environ.get("SNIPSEL_SESSION_SAMESITE", "Lax")
        session_cookie_secure = os.environ.get("SNIPSEL_SESSION_SECURE", "0") == "1"

        cors_raw = os.environ.get("SNIPSEL_CORS_ORIGINS", "")
        cors_origins = [o.strip() for o in cors_raw.split(",") if o.strip()] or [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]

        smtp_host = os.environ.get("SNIPSEL_SMTP_HOST")
        smtp_port = int(os.environ.get("SNIPSEL_SMTP_PORT", "587"))
        smtp_username = os.environ.get("SNIPSEL_SMTP_USERNAME")
        smtp_password = os.environ.get("SNIPSEL_SMTP_PASSWORD")
        smtp_use_tls = os.environ.get("SNIPSEL_SMTP_USE_TLS", "1") == "1"
        mail_from = os.environ.get("SNIPSEL_MAIL_FROM")
        public_base_url = os.environ.get("SNIPSEL_PUBLIC_BASE_URL")

        vapid_private_key = os.environ.get("VAPID_PRIVATE_KEY")
        vapid_public_key = os.environ.get("VAPID_PUBLIC_KEY")
        vapid_subject = os.environ.get("VAPID_SUBJECT")

        return Settings(
            secret_key=secret_key,
            database_url=database_url,
            upload_dir=upload_dir,
            max_upload_bytes=max_upload_bytes,
            session_cookie_samesite=session_cookie_samesite,
            session_cookie_secure=session_cookie_secure,
            cors_origins=cors_origins,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            smtp_use_tls=smtp_use_tls,
            mail_from=mail_from,
            public_base_url=public_base_url,
            vapid_private_key=vapid_private_key,
            vapid_public_key=vapid_public_key,
            vapid_subject=vapid_subject,
        )
