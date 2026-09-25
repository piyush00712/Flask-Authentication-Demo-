from flask import g, render_template

from ..auth.routes import login_required
from . import main_bp


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=g.user)
