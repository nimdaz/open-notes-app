from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# key -> (icon, label). A "markdown" type is planned for a future release.
NOTE_TYPES = {
    "plaintext": ("📝", "Text"),
    "checklist": ("☑️", "Checklist"),
}


class Group(db.Model):
    """Optional container for notes. Notes without a group are shown as "Unsorted"."""

    __tablename__ = "note_group"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    notes = db.relationship("Note", backref="group", lazy=True)


class Note(db.Model):
    __tablename__ = "note"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(20), nullable=False, default="plaintext")
    description = db.Column(db.Text, nullable=True)
    # plaintext: the raw text. checklist: one item per line as "[x] text" / "[ ] text".
    content = db.Column(db.Text, nullable=False, default="")
    group_id = db.Column(db.Integer, db.ForeignKey("note_group.id"), nullable=True)
    starred = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    createdon = db.Column(db.DateTime, default=datetime.now, nullable=False)
    modifiedon = db.Column(db.DateTime, default=datetime.now, nullable=False)
