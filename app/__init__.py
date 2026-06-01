import logging
import os

from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from app.config import Config
from app.extensions import db, jwt, migrate


def _configure_logging(app: Flask) -> None:
    """Set up stdlib logging. Level driven by the LOG_LEVEL env var."""
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

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


def _jwt_error(message: str):
    """Build a JWT error response in the same shape as our other errors."""
    payload = {
        "error": "AuthenticationError",
        "message": message,
        "status": 401,
    }
    response = jsonify(payload)
    response.status_code = 401
    return response


def _register_jwt_callbacks() -> None:
    """Make flask-jwt-extended emit our { error, message, status } shape
    instead of its default {"msg": "..."} response."""

    @jwt.unauthorized_loader
    def _missing_token(_reason):
        return _jwt_error("authentication required")

    @jwt.invalid_token_loader
    def _invalid_token(_reason):
        return _jwt_error("invalid token")

    @jwt.expired_token_loader
    def _expired_token(_jwt_header, _jwt_payload):
        return _jwt_error("token expired")

    @jwt.needs_fresh_token_loader
    def _needs_fresh(_jwt_header, _jwt_payload):
        return _jwt_error("fresh token required")

    @jwt.revoked_token_loader
    def _revoked(_jwt_header, _jwt_payload):
        return _jwt_error("token revoked")


def create_app(config_class: type[Config] = Config) -> Flask:
    load_dotenv()

    app = Flask(__name__)
    app.config.from_object(config_class)

    _configure_logging(app)

    # CORS — open in dev, restrict in prod via CORS_ORIGINS.
    # Explicit allow_headers ensures Authorization (JWT) and X-Registration-Key
    # both pass through the preflight.
    origins_raw = os.environ.get("CORS_ORIGINS", "*").strip()
    cors_kwargs = {
        "allow_headers": ["Content-Type", "Authorization", "X-Registration-Key"],
    }
    if origins_raw == "*":
        CORS(app, **cors_kwargs)
    else:
        origins = [o.strip() for o in origins_raw.split(",") if o.strip()]
        CORS(app, origins=origins, **cors_kwargs)
    app.logger.info("CORS configured (origins=%s)", origins_raw)

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    _register_jwt_callbacks()

    # Import models so Alembic autogenerate sees them
    from app import models  # noqa: F401

    # Blueprints
    from app.controllers.auth import auth_bp
    from app.controllers.workouts import workouts_bp
    from app.controllers.exercise_types import exercise_types_bp
    from app.controllers.exercises import exercises_bp
    from app.controllers.sets import sets_bp
    from app.controllers.errors import register_error_handlers

    app.register_blueprint(auth_bp)
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
