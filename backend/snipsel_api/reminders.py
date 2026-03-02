from __future__ import annotations
from datetime import datetime
from snipsel_api.extensions import db
from snipsel_api import models

def process_reminders(user_id: str | None = None) -> int:
    """Check for due reminders and create notifications. 
    If user_id is None, processes reminders for all users.
    Returns count of new notifications created.
    """
    now = datetime.utcnow()
    
    q = db.select(models.Snipsel).where(
        models.Snipsel.reminder_at.isnot(None),
        models.Snipsel.reminder_at <= now,
        models.Snipsel.deleted_at.is_(None),
        models.Snipsel.task_done == False
    )
    
    if user_id:
        q = q.where(models.Snipsel.owner_user_id == user_id)
        
    due_snipsels = db.session.execute(q).scalars().all()
    
    count = 0
    for s in due_snipsels:
        # Prevent duplicates: Check if ANY notification for this snipsel already exists.
        # We don't check for is_read=False because we only want to notify once per reminder.
        # Recurrence creates NEW snipsels, so they will get their own notifications.
        existing = db.session.execute(
            db.select(models.Notification).where(
                models.Notification.snipsel_id == s.id
            )
        ).scalars().first()
        
        if not existing:
            # Create notification
            n = models.Notification(
                user_id=s.owner_user_id,
                message=f"Reminder: {s.content_markdown[:100] if s.content_markdown else 'Snipsel reminder'}",
                snipsel_id=s.id
            )
            db.session.add(n)
            count += 1
    
    if count > 0:
        db.session.commit()
    return count
