from flask import Flask
import os
import secrets
import logging
from hmac import compare_digest

from flask import abort, request, session

from app.database import init_db


def create_app(database_uri=None):
    environment = os.getenv("APP_ENV", "development").lower()
    configured_secret = os.getenv("SECRET_KEY")
    if environment == "production" and (not configured_secret or len(configured_secret) < 32):
        raise RuntimeError("APP_ENV=production requires SECRET_KEY with at least 32 characters.")

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    app.config.update(
        SECRET_KEY=configured_secret or "dev-only-change-in-production",
        SQLALCHEMY_DATABASE_URI=database_uri or os.getenv("DATABASE_URL", "sqlite:///mindmitra.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=10 * 1024 * 1024,
        UPLOAD_FOLDER=os.path.join(app.instance_path, "uploads"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=(
            os.getenv("SESSION_COOKIE_SECURE", "1" if environment == "production" else "0") == "1"
        ),
    )
    app.logger.setLevel(
        logging.WARNING if environment == "production" else logging.INFO
    )

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    database_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if database_uri and not database_uri.startswith("sqlite"):
        raise RuntimeError(
            "Only SQLite is active in this build. PostgreSQL migration is documented but not configured."
        )
    if database_uri.startswith("sqlite:///"):
        database_path = database_uri.replace("sqlite:///", "", 1)
        if not os.path.isabs(database_path) and "/" not in database_path and "\\" not in database_path:
            os.makedirs(app.instance_path, exist_ok=True)
            database_path = os.path.join(app.instance_path, database_path)
        app.config["DATABASE_PATH"] = database_path
    else:
        app.config["DATABASE_PATH"] = os.path.join(app.instance_path, "mindmitra.db")
    init_db(app)

    @app.before_request
    def csrf_and_session_guard():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)
        if not app.config["TESTING"] and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            if request.path.startswith("/api/") or request.path in {"/login"}:
                supplied = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
                if not supplied or not compare_digest(supplied, session["csrf_token"]):
                    abort(403)

    @app.context_processor
    def inject_template_globals():
        return {
            "csrf_token": session.get("csrf_token", ""),
            "current_role": session.get("role"),
            "current_name": session.get("name"),
        }

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(self), geolocation=()",
        )
        return response

    from app.routes import register_routes

    register_routes(app)
    return app