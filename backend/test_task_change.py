import os
import sys

from snipsel_api.app import create_app
from snipsel_api.extensions import db
from snipsel_api.models import User, Collection, CollectionShare, Notification, Snipsel, Mention, SnipselMention

app = create_app()
with app.app_context():
    u1 = User.query.filter_by(username="test_share1").first()
    u2 = User.query.filter_by(username="test_share2").first()

    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = u1.id
        
    s = Snipsel(owner_user_id=u1.id, type="text", content_markdown="hello @test_share2", created_by_id=u1.id, modified_by_id=u1.id)
    db.session.add(s)
    db.session.commit()
    
    # We must also create mentions via _sync_tags_mentions to simulate proper state before test
    from snipsel_api.routes_snipsels import _sync_tags_mentions
    _sync_tags_mentions(user_id=u1.id, snipsel=s)
    db.session.commit()

    n = Notification.query.filter_by(user_id=u2.id).order_by(Notification.created_at.desc()).first()
    print("Notification after _sync_tags_mentions manually:", n.message if n else "None")
    if n:
        db.session.delete(n)
        db.session.commit()

    res = client.patch(f"/api/snipsels/{s.id}", json={
        "type": "task"
    })
    print("Update (type to task) status:", res.status_code, res.get_json())

    n = Notification.query.filter_by(user_id=u2.id).order_by(Notification.created_at.desc()).first()
    print("Notification after task change:", n.message if n else "None")

