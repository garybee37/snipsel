from __future__ import annotations

import smtplib
from email.message import EmailMessage

from snipsel_api.config import Settings


def send_password_reset_email(*, settings: Settings, to_email: str, token: str) -> None:
    if not settings.smtp_host or not settings.mail_from:
        return

    base = settings.public_base_url or ""
    link = f"{base}/reset-password?token={token}" if base else token

    msg = EmailMessage()
    msg["Subject"] = "snipsel: password reset"
    msg["From"] = settings.mail_from
    msg["To"] = to_email
    msg.set_content(
        "Use the following token/link to reset your password:\n\n"
        f"{link}\n\n"
        "If you did not request this, you can ignore this email."
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_username and settings.smtp_password:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(msg)
