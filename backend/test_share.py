import os
import sys

from snipsel_api.app import create_app
from snipsel_api.extensions import db
from snipsel_api.models import User, Collection, CollectionShare, Notification
from datetime import datetime

app = create_app()
with app.app_context():
    # create test users
    u1 = User.query.filter_by(username="test_share1").first()
    if not u1:
        u1 = User(username="test_share1", email="t1@example.com", password_hash="xx")
        db.session.add(u1)
    
    u2 = User.query.filter_by(username="test_share2").first()
    if not u2:
        u2 = User(username="test_share2", email="t2@example.com", password_hash="xx")
        db.session.add(u2)
        
    db.session.commit()
        
    c = Collection(owner_user_id=u1.id, title="Test Collection", created_by_id=u1.id, modified_by_id=u1.id)
    db.session.add(c)
    db.session.commit()

    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = u1.id

    res = client.post(f"/api/collections/{c.id}/shares", json={
        "shared_with_user_id": u2.id,
        "permission": "read"
    })
    
    print("Share status:", res.status_code)
    
    n = Notification.query.filter_by(user_id=u2.id).order_by(Notification.created_at.desc()).first()
    print("Notification created:", n.message if n else "None")

