from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.services import exercise_service

sets_bp = Blueprint("sets", __name__, url_prefix="/api/sets")


def _user_id() -> int:
    return int(get_jwt_identity())


@sets_bp.put("/<int:set_id>")
@jwt_required()
def update_set(set_id: int):
    data = request.get_json(silent=True) or {}
    exercise_set = exercise_service.update_set(set_id, data, _user_id())
    return jsonify(exercise_set.to_dict())


@sets_bp.delete("/<int:set_id>")
@jwt_required()
def delete_set(set_id: int):
    exercise_service.delete_set(set_id, _user_id())
    return "", 204
