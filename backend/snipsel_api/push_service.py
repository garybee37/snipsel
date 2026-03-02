import json
from pywebpush import webpush, WebPushException

from snipsel_api.extensions import db
from snipsel_api.models import PushSubscription


def send_push_notification(user_id: str, payload: dict):
    from snipsel_api.config import Settings
    settings = Settings.from_env()

    if not settings.vapid_private_key or not settings.vapid_subject:
        return

    # 'sub' claim must be a mailto: link if it's an email address
    vapid_claims = {"sub": settings.vapid_subject}
    if "@" in settings.vapid_subject and not settings.vapid_subject.startswith("mailto:"):
        vapid_claims["sub"] = f"mailto:{settings.vapid_subject}"

    subscriptions = db.session.execute(
        db.select(PushSubscription).where(PushSubscription.user_id == user_id)
    ).scalars().all()

    for sub in subscriptions:
        sub_info = {
            "endpoint": sub.endpoint,
            "keys": {
                "p256dh": sub.keys_p256dh,
                "auth": sub.keys_auth
            }
        }

        try:
            webpush(
                subscription_info=sub_info,
                data=json.dumps(payload),
                vapid_private_key=settings.vapid_private_key,
                vapid_claims=vapid_claims
            )
        except WebPushException as ex:
            # 410 Gone means subscription is invalid/expired
            if ex.response is not None and ex.response.status_code == 410:
                db.session.delete(sub)

    db.session.commit()
