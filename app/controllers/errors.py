from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(HTTPException)
    def handle_http_exception(err: HTTPException):
        response = jsonify(
            {
                "error": err.name,
                "message": err.description,
                "status": err.code,
            }
        )
        response.status_code = err.code or 500
        return response

    @app.errorhandler(Exception)
    def handle_unexpected_exception(err: Exception):
        app.logger.exception("Unhandled exception")
        response = jsonify(
            {
                "error": "Internal Server Error",
                "message": "An unexpected error occurred.",
                "status": 500,
            }
        )
        response.status_code = 500
        return response
