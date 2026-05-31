from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from app.services.errors import ServiceError, ValidationError


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

    @app.errorhandler(ServiceError)
    def handle_service_error(err: ServiceError):
        payload = {
            "error": err.__class__.__name__,
            "message": str(err),
            "status": err.status_code,
        }
        if isinstance(err, ValidationError) and err.field:
            payload["field"] = err.field
        response = jsonify(payload)
        response.status_code = err.status_code
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
