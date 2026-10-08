"""Small helper functions shared across route modules."""

from .models import db, Group, Note, NOTE_TYPES
from .checklist import items_as_text, merge_edited_text

UNSORTED = "unsorted"


def format_datetime(value):
    """e.g. "2026-07-09 14:05" (same format as open-workout-app)."""
    return value.strftime("%Y-%m-%d %H:%M") if value else ""


def all_groups():
    """All groups, alphabetically (case-insensitive). "Unsorted" is not a real group."""
    return Group.query.order_by(db.func.lower(Group.name)).all()


def parse_group_id(raw_value):
    """Return the id of an existing group, or None (= unsorted)."""
    try:
        group_id = int(raw_value)
    except (TypeError, ValueError):
        return None
    return group_id if db.session.get(Group, group_id) else None


def read_checkbox(form, field_name):
    """Interpret an HTML checkbox's presence in submitted form data as a bool."""
    return form.get(field_name) in ("on", "true", "1", "yes")


def query_notes(query_text="", types=None, group=None, starred=False):
    """Notes filtered by title text, note types, and group.

    `group` is None (any group), "unsorted", or a group id. `starred` limits the
    result to starred notes. Newest modified first.
    """
    query = Note.query.filter(Note.type.in_(types if types is not None else list(NOTE_TYPES)))
    if query_text:
        query = query.filter(Note.title.ilike(f"%{query_text}%"))
    if starred:
        query = query.filter(Note.starred.is_(True))
    if group == UNSORTED:
        query = query.filter(Note.group_id.is_(None))
    elif group is not None:
        query = query.filter(Note.group_id == group)
    return query.order_by(Note.modifiedon.desc()).all()


def parse_group_filter(raw_value):
    if raw_value == UNSORTED:
        return UNSORTED
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return None


def content_from_form(note_type, text, old_content=""):
    text = (text or "").replace("\r\n", "\n")
    return merge_edited_text(old_content, text) if note_type == "checklist" else text


def edit_text_for(note):
    if note is None:
        return ""
    return items_as_text(note.content) if note.type == "checklist" else note.content
