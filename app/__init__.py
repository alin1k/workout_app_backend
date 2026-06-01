import logging
import os

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from app.config import Config
from app.extensions import db, migrate


def _configure_logging(app: Flask) -> None:
    """Set up stdlib logging. Level driven by the LOG_LEVEL env var."""
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    # Reconfigure root logger so our format wins even if something
    # (e.g. werkzeug, alembic) configured it earlier.
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    app.logger.setLevel(level)
    logging.getLogger("app").setLevel(level)


def create_app(config_class: type[Config] = Config) -> Flask:
    load_dotenv()

    app = Flask(__name__)
    app.config.from_object(config_class)

    _configure_logging(app)

    # CORS — open in dev, restrict in prod by setting CORS_ORIGINS to a
    # comma-separated list of allowed origins (e.g. "https://app.example.com").
    origins_raw = os.environ.get("CORS_ORIGINS", "*").strip()
    if origins_raw == "*":
        CORS(app)
    else:
        origins = [o.strip() for o in origins_raw.split(",") if o.strip()]
        CORS(app, origins=origins)
    app.logger.info("CORS configured (origins=%s)", origins_raw)

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Import models so Alembic autogenerate sees them
    from app import models  # noqa: F401

    # Blueprints
    from app.controllers.workouts import workouts_bp
    from app.controllers.exercise_types import exercise_types_bp
    from app.controllers.exercises import exercises_bp
    from app.controllers.sets import sets_bp
    from app.controllers.errors import register_error_handlers

    app.register_blueprint(workouts_bp)
    app.register_blueprint(exercise_types_bp)
    app.register_blueprint(exercises_bp)
    app.register_blueprint(sets_bp)

    register_error_handlers(app)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    app.logger.info("App initialized (env=%s)", app.config.get("ENV"))
    return app
