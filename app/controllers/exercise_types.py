from flask import Blueprint, jsonify, request

from app.services import exercise_type_service

exercise_types_bp = Blueprint("exercise_types", __name__, url_prefix="/api/exercise-types")


@exercise_types_bp.get("")
def list_exercise_types():
    items = exercise_type_service.list_exercise_types()
    return jsonify([et.to_dict() for et in items])


@exercise_types_bp.post("")
def create_exercise_type():
    data = request.get_json(silent=True) or {}
    et = exercise_type_service.create_exercise_type(data)
    return jsonify(et.to_dict()), 201


@exercise_types_bp.get("/<int:et_id>")
def get_exercise_type(et_id: int):
    et = exercise_type_service.get_exercise_type(et_id)
    return jsonify(et.to_dict())


@exercise_types_bp.put("/<int:et_id>")
def update_exercise_type(et_id: int):
    data = request.get_json(silent=True) or {}
    et = exercise_type_service.update_exercise_type(et_id, data)
    return jsonify(et.to_dict())


@exercise_types_bp.delete("/<int:et_id>")
def delete_exercise_type(et_id: int):
    exercise_type_service.delete_exercise_type(et_id)
    return "", 204
