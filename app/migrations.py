"""Tiny schema upgrades for databases created by older versions.

db.create_all() only creates missing tables, so columns added in later
versions are added here with ALTER TABLE.
"""

from sqlalchemy import inspect, text

from .models import db


def ensure_schema():
    note_columns = {column["name"] for column in inspect(db.engine).get_columns("note")}
    if "starred" not in note_columns:  # added in 0.0.4
        db.session.execute(text("ALTER TABLE note ADD COLUMN starred BOOLEAN NOT NULL DEFAULT 0"))
        db.session.commit()
