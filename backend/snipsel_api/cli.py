from __future__ import annotations

from flask.cli import FlaskGroup

from snipsel_api.app import create_app
from snipsel_api.extensions import db
from snipsel_api import models


def _create_app():
    return create_app()


cli = FlaskGroup(create_app=_create_app)


@cli.command("db-init")
def db_init():
    app = create_app()
    with app.app_context():
        db.create_all()
