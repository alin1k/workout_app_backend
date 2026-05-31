from flask import Blueprint, jsonify

from app.extensions import db
from app.models.exercise_set import ExerciseSet

sets_bp = Blueprint("sets", __name__, url_prefix="/api/sets")


@sets_bp.delete("/<int:set_id>")
def delete_set(set_id: int):
    exercise_set = db.session.get(ExerciseSet, set_id)
    if not exercise_set:
        return jsonify({"error": "set not found"}), 404
    db.session.delete(exercise_set)
    db.session.commit()
    return "", 204
