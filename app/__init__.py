from flask import Flask
from dotenv import load_dotenv

from app.config import Config
from app.extensions import db, migrate


def create_app(config_class: type[Config] = Config) -> Flask:
    load_dotenv()

    app = Flask(__name__)
    app.config.from_object(config_class)

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

    return app
