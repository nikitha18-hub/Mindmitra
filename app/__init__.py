from flask import Flask
import os

from app.database import init_db


def create_app(database_uri=None):
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    app.config.update(
        SECRET_KEY="dev-only-change-in-production",
        SQLALCHEMY_DATABASE_URI=database_uri or os.getenv("DATABASE_URL", "sqlite:///mindmitra.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=10 * 1024 * 1024,
        UPLOAD_FOLDER=os.path.join(app.instance_path, "uploads"),
    )

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    database_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if database_uri.startswith("sqlite:///"):
        database_path = database_uri.replace("sqlite:///", "", 1)
        if not os.path.isabs(database_path) and "/" not in database_path and "\\" not in database_path:
            os.makedirs(app.instance_path, exist_ok=True)
            database_path = os.path.join(app.instance_path, database_path)
        app.config["DATABASE_PATH"] = database_path
    else:
        app.config["DATABASE_PATH"] = os.path.join(app.instance_path, "mindmitra.db")
    init_db(app)

    from app.routes import register_routes

    register_routes(app)
    return app