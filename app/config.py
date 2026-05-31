import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    ENV = os.environ.get("FLASK_ENV", "development")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:dev@localhost:5433/workout_app",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
