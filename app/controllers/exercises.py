from flask import Blueprint, jsonify, request

from app.services import exercise_service

exercises_bp = Blueprint("exercises", __name__, url_prefix="/api/exercises")


@exercises_bp.delete("/<int:exercise_id>")
def delete_exercise(exercise_id: int):
    exercise_service.delete_exercise(exercise_id)
    return "", 204


@exercises_bp.post("/<int:exercise_id>/sets")
def add_set(exercise_id: int):
    data = request.get_json(silent=True) or {}
    exercise_set = exercise_service.add_set(exercise_id, data)
    return jsonify(exercise_set.to_dict()), 201
