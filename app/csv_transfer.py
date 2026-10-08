"""CSV export and import for backing up and restoring groups and notes."""

import csv
import io
from datetime import datetime

from .models import db, Group, Note, NOTE_TYPES
from .helpers import UNSORTED

CSV_COLUMNS = ["type", "name", "title", "note_type", "group", "description", "content",
               "createdon", "modifiedon", "starred"]


def export_all_data_as_csv():
    """Return a CSV string containing every group and note."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(CSV_COLUMNS)

    for group in Group.query.order_by(Group.id).all():
        writer.writerow(["group", group.name, "", "", "", group.description or "", "", "", "", ""])

    for note in Note.query.order_by(Note.id).all():
        writer.writerow([
            "note", "", note.title, note.type, note.group.name if note.group else "",
            note.description or "", note.content,
            note.createdon.isoformat(sep=" "), note.modifiedon.isoformat(sep=" "),
            int(note.starred),
        ])
    return output.getvalue()


def import_data_from_csv(file_stream):
    """Import groups and notes from a CSV produced by export_all_data_as_csv().

    Groups are matched by name and reused; notes are always added as new rows.
    Returns a human-readable summary message, or an error message on failure.
    """
    try:
        reader = csv.DictReader(io.StringIO(file_stream.read().decode("utf-8-sig")))
        groups_by_name = {group.name.lower(): group for group in Group.query.all()}
        group_count = 0
        note_count = 0

        for row in reader:
            row_type = (row.get("type") or "").strip().lower()
            if row_type == "group":
                group_count += _get_or_create_group(row.get("name"), row.get("description"), groups_by_name)[1]
            elif row_type == "note":
                note_count += _import_note_row(row, groups_by_name)

        db.session.commit()
        return f"Imported {group_count} group(s) and {note_count} note(s)."
    except Exception as error:
        db.session.rollback()
        return f"Import failed: {error}"


def _get_or_create_group(name, description, groups_by_name):
    """Return (group, created) where created is 1 if a group was added."""
    name = (name or "").strip()
    if not name or name.lower() == UNSORTED:
        return None, 0
    group = groups_by_name.get(name.lower())
    if group:
        return group, 0
    group = Group(name=name, description=(description or "").strip() or None)
    db.session.add(group)
    db.session.flush()
    groups_by_name[name.lower()] = group
    return group, 1


def _parse_timestamp(raw_value):
    try:
        return datetime.fromisoformat((raw_value or "").strip())
    except ValueError:
        return datetime.now()


def _import_note_row(row, groups_by_name):
    title = (row.get("title") or "").strip()
    if not title:
        return 0
    group, _ = _get_or_create_group(row.get("group"), "", groups_by_name)
    note_type = (row.get("note_type") or "").strip()
    db.session.add(Note(
        title=title,
        type=note_type if note_type in NOTE_TYPES else "plaintext",
        description=(row.get("description") or "").strip() or None,
        content=row.get("content") or "",
        group_id=group.id if group else None,
        starred=(row.get("starred") or "").strip() in ("1", "true", "True", "yes"),
        createdon=_parse_timestamp(row.get("createdon")),
        modifiedon=_parse_timestamp(row.get("modifiedon")),
    ))
    return 1
