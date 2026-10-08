"""Top-level pages that aren't tied to a specific resource: home and about."""

from flask import Blueprint, render_template

bp = Blueprint("pages", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/about")
def about():
    return render_template("about.html")
