import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    ENV = os.environ.get("FLASK_ENV", "development")
