"""Flask application factory. Run with flask --app app:create_app run."""
import os
from datetime import timedelta

from flask import Flask, jsonify, request
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException

from extensions import bcrypt, db, migrate
from security import protect_browser_requests


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///notes.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
        MAX_CONTENT_LENGTH=64 * 1024,
        FRONTEND_ORIGIN=os.environ.get("FRONTEND_ORIGIN", "").rstrip("/"),
    )
    if test_config:
        app.config.update(test_config)
    if not app.config["SECRET_KEY"] or app.config["SECRET_KEY"] == "replace-with-a-random-secret":
        raise RuntimeError("Set SECRET_KEY to a private random value before starting the API.")
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    app.before_request(protect_browser_requests)
    from routes.auth import auth
    from routes.notes import notes
    app.register_blueprint(auth)
    app.register_blueprint(notes)

    @app.errorhandler(ValidationError)
    def validation_error(error):
        return jsonify(errors=error.messages), 422

    @app.errorhandler(HTTPException)
    def http_error(error):
        response = error.get_response()
        response.data = app.json.dumps({"error": error.description})
        response.content_type = "application/json"
        return response

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify(error="An internal server error occurred."), 500

    @app.after_request
    def response_headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        if app.config["FRONTEND_ORIGIN"]:
            response.vary.add("Origin")
        origin = request.headers.get("Origin")
        if origin and origin == app.config["FRONTEND_ORIGIN"]:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-CSRF-Token"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, DELETE, OPTIONS"
            response.headers["Access-Control-Expose-Headers"] = "Location"
        return response

    return app


if __name__ == "__main__":
    create_app().run(port=5555)
