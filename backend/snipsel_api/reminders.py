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
            models.Snipsel.deleted_at.is_(None)
        )
    ).scalars().all()
    
    count = 0
    for s in due_snipsels:
        # Create notification
        n = models.Notification(
            user_id=s.owner_user_id,
            message=f"Reminder: {s.content_markdown[:100] if s.content_markdown else 'Snipsel reminder'}",
            snipsel_id=s.id
        )
        db.session.add(n)
        
        # Handle recurrence
        if s.reminder_rrule:
            try:
                # Parse rrule and find next occurrence
                rr = rrule.rrulestr(s.reminder_rrule, dtstart=s.reminder_at)
                next_at = rr.after(now)
                s.reminder_at = next_at
            except Exception:
                # If rrule parsing fails, we keep the old date as "expired"
                pass
        
        count += 1
    
    if count > 0:
        db.session.commit()
    return count
