from __future__ import annotations

from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from flask_apscheduler import APScheduler

db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
scheduler = APScheduler()
