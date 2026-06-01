from flask import Blueprint, jsonify, request

from app.services import exercise_service

sets_bp = Blueprint("sets", __name__, url_prefix="/api/sets")


@sets_bp.put("/<int:set_id>")
def update_set(set_id: int):
    data = request.get_json(silent=True) or {}
    exercise_set = exercise_service.update_set(set_id, data)
    return jsonify(exercise_set.to_dict())


@sets_bp.delete("/<int:set_id>")
def delete_set(set_id: int):
    exercise_service.delete_set(set_id)
    return "", 204
