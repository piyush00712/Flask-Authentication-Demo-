from flask import Blueprint

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

from . import routes  # noqa: E402,F401  (registers routes on auth_bp)
