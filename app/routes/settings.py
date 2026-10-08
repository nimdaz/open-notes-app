"""Settings page plus CSV export/import and full data removal."""

from flask import Blueprint, render_template, request, Response

from ..models import db, Group, Note
from ..csv_transfer import export_all_data_as_csv, import_data_from_csv

bp = Blueprint("settings", __name__)

REQUIRED_CONFIRMATION_TEXT = "confirm"


@bp.route("/settings")
def settings_page():
    return render_template("settings.html")


@bp.route("/export/csv")
def export_csv():
    return Response(
        export_all_data_as_csv(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=notes-data.csv"},
    )


@bp.route("/import/csv", methods=["POST"])
def import_csv():
    uploaded_file = request.files.get("file")
    if not uploaded_file or uploaded_file.filename == "":
        return render_template("settings.html", message="No file selected.")
    message = import_data_from_csv(uploaded_file.stream)
    return render_template("settings.html", message=message)


@bp.route("/settings/delete-all", methods=["POST"])
def delete_all_data():
    typed_confirmation = request.form.get("confirm", "").strip().lower()
    if typed_confirmation != REQUIRED_CONFIRMATION_TEXT:
        return render_template(
            "settings.html",
            message='Type "confirm" exactly to remove all data. Nothing was deleted.',
        )
    Note.query.delete()
    Group.query.delete()
    db.session.commit()
    return render_template("settings.html", message="All data has been removed.")
