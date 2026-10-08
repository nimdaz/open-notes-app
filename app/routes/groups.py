"""Routes for creating, browsing, editing, and deleting groups.

"Unsorted" is not a stored group: it stands for notes without a group and is
always listed first.
"""

from flask import Blueprint, render_template, request, redirect, url_for

from ..models import db, Group, Note
from ..helpers import all_groups, query_notes, UNSORTED

bp = Blueprint("groups", __name__, url_prefix="/groups")


@bp.route("/")
def groups_list():
    unsorted_count = Note.query.filter(Note.group_id.is_(None)).count()
    return render_template("groups.html", groups=all_groups(), unsorted_count=unsorted_count)


@bp.route("/unsorted")
def group_unsorted():
    return render_template("group_detail.html", group=None, notes=query_notes(group=UNSORTED))


@bp.route("/<int:group_id>")
def group_detail(group_id):
    group = Group.query.get_or_404(group_id)
    return render_template("group_detail.html", group=group, notes=query_notes(group=group.id))


def _name_error(name, own_id=None):
    if not name:
        return "Please enter a name."
    if name.lower() == UNSORTED:
        return '"Unsorted" is reserved for notes without a group.'
    existing = Group.query.filter(db.func.lower(Group.name) == name.lower()).first()
    if existing and existing.id != own_id:
        return f'A group named "{name}" already exists.'
    return None


@bp.route("/new")
def group_new_page():
    return render_template("group_form.html", is_edit=False, group_id=None,
                           name=request.args.get("name", ""), description="")


@bp.route("/new", methods=["POST"])
def group_create():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip() or None
    error = _name_error(name)
    if error:
        return render_template("group_form.html", is_edit=False, group_id=None,
                               name=name, description=description, error=error)
    group = Group(name=name, description=description)
    db.session.add(group)
    db.session.commit()
    return redirect(url_for("groups.groups_list"))


@bp.route("/<int:group_id>/edit")
def group_edit_page(group_id):
    group = Group.query.get_or_404(group_id)
    return render_template("group_form.html", is_edit=True, group_id=group.id,
                           name=group.name, description=group.description)


@bp.route("/<int:group_id>/edit", methods=["POST"])
def group_update(group_id):
    group = Group.query.get_or_404(group_id)
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip() or None
    error = _name_error(name, own_id=group.id)
    if error:
        return render_template("group_form.html", is_edit=True, group_id=group.id,
                               name=name, description=description, error=error)
    group.name = name
    group.description = description
    db.session.commit()
    return redirect(url_for("groups.group_detail", group_id=group.id))


@bp.route("/<int:group_id>/delete", methods=["POST"])
def group_delete(group_id):
    group = Group.query.get_or_404(group_id)
    Note.query.filter_by(group_id=group.id).update({"group_id": None})  # notes become unsorted
    db.session.delete(group)
    db.session.commit()
    return redirect(url_for("groups.groups_list"))
