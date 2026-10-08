"""Application factory: creates and configures the Flask app.

The SQLite database file lives under DATA_DIR (default: app/data), which is
meant to be mounted as a volume when running in Docker so data survives
container restarts.
"""

import os

from flask import Flask

from .helpers import format_datetime
from .migrations import ensure_schema
from .models import db, NOTE_TYPES
from .routes import ALL_BLUEPRINTS
from .version import APP_VERSION


def create_app():
    app = Flask(__name__)

    data_dir = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
    os.makedirs(data_dir, exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(data_dir, "app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # CSV import limit

    db.init_app(app)
    with app.app_context():
        db.create_all()
        ensure_schema()

    for blueprint in ALL_BLUEPRINTS:
        app.register_blueprint(blueprint)

    app.add_template_filter(format_datetime, "dt")

    @app.context_processor
    def inject_template_globals():
        return {"app_version": APP_VERSION, "note_types": NOTE_TYPES}

    return app
