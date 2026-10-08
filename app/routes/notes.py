"""Routes for creating, browsing, editing, and deleting notes."""

import json
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, make_response, abort

from ..models import db, Note, NOTE_TYPES
from ..checklist import parse_items, dump_items
from ..helpers import (all_groups, parse_group_id, parse_group_filter, query_notes,
                       content_from_form, edit_text_for, format_datetime, read_checkbox)

bp = Blueprint("notes", __name__, url_prefix="/notes")


@bp.route("/")
def notes_list():
    return render_template("notes.html", notes=query_notes())


@bp.route("/search")
def note_search():
    """Partial used by htmx: title search plus type toggles (and optional group)."""
    query_text = request.args.get("q", "").strip()
    types = [t for t in request.args.getlist("t") if t in NOTE_TYPES]
    group = parse_group_filter(request.args.get("group"))
    starred = request.args.get("starred") == "1"
    return render_template("_note_list.html", notes=query_notes(query_text, types, group, starred))


@bp.route("/starred")
def notes_starred():
    return render_template("starred.html", notes=query_notes(starred=True))


@bp.route("/new")
def note_new_page():
    return render_template(
        "note_new.html", note=None, groups=all_groups(), edit_content="",
        selected_group=request.args.get("group", type=int),
        note_type=request.args.get("type", "plaintext"), title=request.args.get("title", ""),
    )


@bp.route("/new", methods=["POST"])
def note_create():
    note_type = request.form.get("type", "plaintext")
    if note_type not in NOTE_TYPES:
        note_type = "plaintext"
    note = Note(
        title=request.form.get("title", "").strip() or "Untitled",
        type=note_type,
        description=request.form.get("description", "").strip() or None,
        group_id=parse_group_id(request.form.get("group_id")),
        content=content_from_form(note_type, request.form.get("content", "")),
    )
    db.session.add(note)
    db.session.commit()
    return redirect(url_for("notes.note_detail", note_id=note.id))


@bp.route("/<int:note_id>")
def note_detail(note_id):
    note = Note.query.get_or_404(note_id)
    items = parse_items(note.content) if note.type == "checklist" else []
    # Fallback for the "back" button when there is no previous page to return to.
    back_url = (url_for("groups.group_detail", group_id=note.group_id) if note.group_id
                else url_for("notes.notes_list"))
    return render_template(
        "note_detail.html", note=note, items=items, groups=all_groups(),
        selected_group=note.group_id, edit_content=edit_text_for(note), back_url=back_url,
    )


@bp.route("/<int:note_id>/edit", methods=["POST"])
def note_update(note_id):
    """Save the note's content (edit mode: auto-save, leaving edit mode, going back)."""
    note = Note.query.get_or_404(note_id)
    note.content = content_from_form(note.type, request.form.get("content", ""), note.content)
    note.modifiedon = datetime.now()
    db.session.commit()
    if request.headers.get("X-Fetch"):
        return {"ok": True, "modified": format_datetime(note.modifiedon)}
    return redirect(url_for("notes.note_detail", note_id=note.id))


@bp.route("/<int:note_id>/details", methods=["POST"])
def note_update_details(note_id):
    """Save title, group and description (the "Note details" panel)."""
    note = Note.query.get_or_404(note_id)
    note.title = request.form.get("title", "").strip() or note.title
    note.description = request.form.get("description", "").strip() or None
    note.group_id = parse_group_id(request.form.get("group_id"))
    note.starred = read_checkbox(request.form, "starred")
    note.modifiedon = datetime.now()
    db.session.commit()
    if request.headers.get("X-Fetch"):
        return {"ok": True, "title": note.title, "starred": note.starred,
                "modified": format_datetime(note.modifiedon)}
    return redirect(url_for("notes.note_detail", note_id=note.id))


@bp.route("/<int:note_id>/star", methods=["POST"])
def note_toggle_star(note_id):
    """Star / unstar a note. Starring is not a content change, so modifiedon stays."""
    note = Note.query.get_or_404(note_id)
    note.starred = not note.starred
    db.session.commit()
    if request.headers.get("HX-Request"):  # list rows: swap in the new button
        return render_template("_star_button.html", note=note)
    if request.headers.get("X-Fetch"):  # note page
        return {"ok": True, "starred": note.starred}
    return redirect(url_for("notes.note_detail", note_id=note.id))


@bp.route("/<int:note_id>/toggle/<int:item_index>", methods=["POST"])
def note_toggle_item(note_id, item_index):
    """Flip one checklist item and save right away."""
    note = Note.query.get_or_404(note_id)
    items = parse_items(note.content)
    if note.type != "checklist" or item_index >= len(items):
        abort(400)
    done, text = items[item_index]
    items[item_index] = (not done, text)
    note.content = dump_items(items)
    note.modifiedon = datetime.now()
    db.session.commit()
    response = make_response("")
    response.headers["HX-Trigger"] = json.dumps({"saved": {"modified": format_datetime(note.modifiedon)}})
    return response


@bp.route("/<int:note_id>/delete", methods=["POST"])
def note_delete(note_id):
    note = Note.query.get_or_404(note_id)
    group_id = note.group_id
    db.session.delete(note)
    db.session.commit()
    if group_id:
        return redirect(url_for("groups.group_detail", group_id=group_id))
    return redirect(url_for("notes.notes_list"))
