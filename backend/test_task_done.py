import os
import sys

from snipsel_api.app import create_app
from snipsel_api.extensions import db
from snipsel_api.models import User, Collection, Notification, Snipsel

app = create_app()
with app.app_context():
    u1 = User.query.filter_by(username="test_share1").first() # creator
    u2 = User.query.filter_by(username="test_share2").first() # completor

    client = app.test_client()
    
    # u1 creates task
    with client.session_transaction() as sess:
        sess['user_id'] = u1.id
        
    s = Snipsel(owner_user_id=u1.id, type="task", content_markdown="finish the test", created_by_id=u1.id, modified_by_id=u1.id)
    db.session.add(s)
    db.session.commit()
    
    # clear u1 notifications
    for n in Notification.query.filter_by(user_id=u1.id).all():
        db.session.delete(n)
    db.session.commit()

    # u2 completes task
    with client.session_transaction() as sess:
        sess['user_id'] = u2.id
        
    # Assume u2 has access for this test (we mock it indirectly via the endpoint or bypass collection check)
    # The endpoint checks has_write_access which calls can_write_snipsel_via_collections.
    # To make the test simple, let's just make u2 owner temporally
    s.owner_user_id = u2.id
    db.session.commit()

    res = client.patch(f"/api/snipsels/{s.id}", json={
        "task_done": True
    })
    print("Update status:", res.status_code)

    n = Notification.query.filter_by(user_id=u1.id).order_by(Notification.created_at.desc()).first()
    print("Notification to u1:", n.message if n else "None")

