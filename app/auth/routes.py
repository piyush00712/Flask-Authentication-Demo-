import functools
import sqlite3

from flask import flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from ..db import get_db
from . import auth_bp


def login_required(view):
    """Route decorator: redirects to login if there's no authenticated user in session."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.get("user") is None:
            flash("Please log in to access that page.")
            return redirect(url_for("auth.login"))
        return view(**kwargs)
    return wrapped_view


@auth_bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            "SELECT id, username FROM user WHERE id = ?", (user_id,)
        ).fetchone()


@auth_bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        error = None

        if not username:
            error = "Username is required."
        elif not password or len(password) < 6:
            error = "Password must be at least 6 characters."

        if error is None:
            db = get_db()
            try:
                db.execute(
                    "INSERT INTO user (username, password_hash) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
            except sqlite3.IntegrityError:
                error = f"User {username} is already registered."
            else:
                flash("Registration successful. Please log in.")
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        db = get_db()
        error = None

        user = db.execute(
            "SELECT * FROM user WHERE username = ?", (username,)
        ).fetchone()

        if user is None:
            error = "Incorrect username or password."
        elif not check_password_hash(user["password_hash"], password):
            error = "Incorrect username or password."

        if error is None:
            session.clear()
            session["user_id"] = user["id"]
            flash(f"Welcome back, {user['username']}!")
            return redirect(url_for("main.dashboard"))

        flash(error)

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("auth.login"))
