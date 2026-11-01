"""Session authentication and browser request forgery protection."""
from functools import wraps
from hmac import compare_digest

from flask import abort, current_app, g, request, session

from extensions import db
from models import User


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        g.user = db.session.get(User, user_id) if user_id else None
        if g.user is None:
            session.clear()
            abort(401, description="Authentication required.")
        return view(*args, **kwargs)
    return wrapped


def protect_browser_requests():
    """JSON-only writes block HTML forms; origin and CSRF checks protect sessions."""
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    origin = request.headers.get("Origin")
    allowed = {request.host_url.rstrip("/")}
    if current_app.config["FRONTEND_ORIGIN"]:
        allowed.add(current_app.config["FRONTEND_ORIGIN"])
    if origin and origin not in allowed:
        abort(403, description="Origin is not allowed.")
    if request.headers.get("Sec-Fetch-Site") == "cross-site" and not origin:
        abort(403, description="Cross-site request rejected.")
    if not request.is_json:
        abort(415, description="Content-Type must be application/json, including DELETE requests.")
    if session.get("user_id"):
        expected = session.get("csrf_token", "")
        supplied = request.headers.get("X-CSRF-Token", "")
        if not expected or not compare_digest(expected.encode(), supplied.encode()):
            abort(403, description="A valid X-CSRF-Token header is required.")
