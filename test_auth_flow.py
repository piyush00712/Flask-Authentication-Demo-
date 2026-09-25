"""
Exercises the real authentication flow end-to-end using Flask's test client
(no mocking): register -> login with correct/incorrect passwords ->
access protected route -> logout -> confirm route is blocked again.

Run: python test_auth_flow.py
"""
import sys
import tempfile
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app  # noqa: E402


def run():
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({"TESTING": True, "DATABASE": db_path, "SECRET_KEY": "test"})
    client = app.test_client()

    checks = []

    def check(name, condition):
        checks.append((name, condition))
        print(f"{'PASS' if condition else 'FAIL'}: {name}")

    # Dashboard should redirect to login when not authenticated
    r = client.get("/dashboard", follow_redirects=True)
    check("unauthenticated dashboard access redirects to login", b"Log in" in r.data)

    # Register a new user
    r = client.post("/auth/register", data={"username": "alice", "password": "correcthorse"}, follow_redirects=True)
    check("registration succeeds", b"Registration successful" in r.data or r.status_code == 200)

    # Duplicate registration should fail
    r = client.post("/auth/register", data={"username": "alice", "password": "anotherpass"}, follow_redirects=True)
    check("duplicate username is rejected", b"already registered" in r.data)

    # Wrong password should fail
    r = client.post("/auth/login", data={"username": "alice", "password": "wrongpassword"}, follow_redirects=True)
    check("wrong password is rejected", b"Incorrect username or password" in r.data)

    # Correct login should succeed and allow dashboard access
    r = client.post("/auth/login", data={"username": "alice", "password": "correcthorse"}, follow_redirects=True)
    check("correct login succeeds", b"Welcome back" in r.data)

    r = client.get("/dashboard")
    check("authenticated user can access dashboard", b"Dashboard" in r.data and b"alice" in r.data)

    # Logout, then dashboard should be blocked again
    client.get("/auth/logout")
    r = client.get("/dashboard", follow_redirects=True)
    check("after logout, dashboard is blocked again", b"Log in" in r.data)

    # Verify password is actually hashed in the DB, not stored in plaintext
    with app.app_context():
        from app.db import get_db
        row = get_db().execute("SELECT password_hash FROM user WHERE username = 'alice'").fetchone()
        check("password is hashed, not stored in plaintext", row["password_hash"] != "correcthorse" and row["password_hash"].startswith(("pbkdf2:", "scrypt:")))

    os.close(db_fd)
    os.unlink(db_path)

    failed = [name for name, ok in checks if not ok]
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
    if failed:
        print("FAILED:", failed)
        sys.exit(1)
    else:
        print("All checks passed.")


if __name__ == "__main__":
    run()
