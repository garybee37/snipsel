from __future__ import annotations
from datetime import datetime
from dateutil import rrule
from snipsel_api.extensions import db
from snipsel_api import models

def process_reminders(user_id: str) -> int:
    """Check for due reminders and create notifications for a specific user. Returns count of processed reminders."""
    now = datetime.utcnow()
    due_snipsels = db.session.execute(
        db.select(models.Snipsel).where(
            models.Snipsel.owner_user_id == user_id,
            models.Snipsel.reminder_at.isnot(None),
            models.Snipsel.reminder_at <= now,
            models.Snipsel.deleted_at.is_(None),
            models.Snipsel.task_done == False
        )
    ).scalars().all()
    
    count = 0
    for s in due_snipsels:
        # Prevent duplicates: Check if an unread notification for this snipsel already exists
        existing = db.session.execute(
            db.select(models.Notification).where(
                models.Notification.snipsel_id == s.id,
                models.Notification.is_read == False
            )
        ).scalars().first()
        
        if existing:
            # Skip creating a new notification if one already exists and is unread
            pass
        else:
            # Create notification
            n = models.Notification(
                user_id=s.owner_user_id,
                message=f"Reminder: {s.content_markdown[:100] if s.content_markdown else 'Snipsel reminder'}",
                snipsel_id=s.id
            )
            db.session.add(n)
        
        # [REMOVED] Handle recurrence automatically. 
        # Recurrence is now handled in update_snipsel when a task is marked as done.
        
        count += 1
    
    if count > 0:
        db.session.commit()
    return count
