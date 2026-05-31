from flask import Blueprint

from app.services import exercise_service

sets_bp = Blueprint("sets", __name__, url_prefix="/api/sets")


@sets_bp.delete("/<int:set_id>")
def delete_set(set_id: int):
    exercise_service.delete_set(set_id)
    return "", 204
