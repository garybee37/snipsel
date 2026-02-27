from __future__ import annotations

from flask.cli import FlaskGroup

from snipsel_api.app import create_app
from snipsel_api.extensions import db
from snipsel_api import models
from snipsel_api.routes_attachments import _resolve_attachment_path, _resolve_thumbnail_path


def _create_app():
    return create_app()


cli = FlaskGroup(create_app=_create_app)


@cli.command("db-init")
def db_init():
    app = create_app()
    with app.app_context():
        db.create_all()


@cli.command("cleanup")
def cleanup():
    """Completely delete all snipsels and collections marked as deleted, including attachments."""
    app = create_app()
    with app.app_context():
        deleted_snipsels = db.session.execute(
            db.select(models.Snipsel).where(models.Snipsel.deleted_at.isnot(None))
        ).scalars().all()
        
        snipsel_count = len(deleted_snipsels)
        attachment_count = 0
        
        for snipsel in deleted_snipsels:
            for att in snipsel.attachments:
                file_path = _resolve_attachment_path(att)
                thumb_path = _resolve_thumbnail_path(att)
                
                for p in [thumb_path, file_path]:
                    if not p:
                        continue
                    try:
                        p.unlink(missing_ok=True)
                        attachment_count += 1
                    except OSError:
                        pass
                
                db.session.delete(att)
            
            # Delete related entities explicitly to avoid foreign key constraint errors
            db.session.execute(db.delete(models.CollectionSnipsel).where(models.CollectionSnipsel.snipsel_id == snipsel.id))
            db.session.execute(db.delete(models.SnipselTag).where(models.SnipselTag.snipsel_id == snipsel.id))
            db.session.execute(db.delete(models.SnipselMention).where(models.SnipselMention.snipsel_id == snipsel.id))
            db.session.execute(db.delete(models.SnipselLink).where((models.SnipselLink.from_snipsel_id == snipsel.id) | (models.SnipselLink.to_snipsel_id == snipsel.id)))
            db.session.execute(db.delete(models.SnipselCollectionRef).where(models.SnipselCollectionRef.snipsel_id == snipsel.id))
            db.session.execute(db.delete(models.Notification).where(models.Notification.snipsel_id == snipsel.id))
            
            db.session.delete(snipsel)
        
        deleted_collections = db.session.execute(
            db.select(models.Collection).where(models.Collection.deleted_at.isnot(None))
        ).scalars().all()
        
        collection_count = len(deleted_collections)
        
        for collection in deleted_collections:
            db.session.execute(db.delete(models.CollectionSnipsel).where(models.CollectionSnipsel.collection_id == collection.id))
            db.session.execute(db.delete(models.CollectionShare).where(models.CollectionShare.collection_id == collection.id))
            db.session.execute(db.delete(models.CollectionFavorite).where(models.CollectionFavorite.collection_id == collection.id))
            db.session.execute(db.delete(models.SnipselCollectionRef).where(models.SnipselCollectionRef.collection_id == collection.id))
            db.session.execute(db.delete(models.Notification).where(models.Notification.collection_id == collection.id))
            db.session.execute(db.delete(models.CollectionVisit).where(models.CollectionVisit.collection_id == collection.id))
            
            # nullify day_collection_template_id in users
            db.session.execute(
                db.update(models.User)
                .where(models.User.day_collection_template_id == collection.id)
                .values(day_collection_template_id=None)
            )

            db.session.delete(collection)

        db.session.commit()
        print(f"Cleanup complete: {snipsel_count} snipsels, {collection_count} collections, and {attachment_count} attachment files deleted.")
