from flask import Blueprint, jsonify, request
from sqlalchemy import func

from app.extensions import db
from app.models.exercise import Exercise
from app.models.exercise_set import ExerciseSet

exercises_bp = Blueprint("exercises", __name__, url_prefix="/api/exercises")


@exercises_bp.delete("/<int:exercise_id>")
def delete_exercise(exercise_id: int):
    exercise = db.session.get(Exercise, exercise_id)
    if not exercise:
        return jsonify({"error": "exercise not found"}), 404
    db.session.delete(exercise)
    db.session.commit()
    return "", 204


@exercises_bp.post("/<int:exercise_id>/sets")
def add_set(exercise_id: int):
    exercise = db.session.get(Exercise, exercise_id)
    if not exercise:
        return jsonify({"error": "exercise not found"}), 404

    data = request.get_json(silent=True) or {}
    if data.get("reps") is None:
        return jsonify({"error": "reps is required"}), 400

    if "set_number" in data:
        set_number = int(data["set_number"])
    else:
        max_number = (
            db.session.query(func.max(ExerciseSet.set_number))
            .filter(ExerciseSet.exercise_id == exercise_id)
            .scalar()
        )
        set_number = (max_number or 0) + 1

    weight = data.get("weight")
    exercise_set = ExerciseSet(
        exercise_id=exercise_id,
        set_number=set_number,
        reps=int(data["reps"]),
        weight=float(weight) if weight is not None else None,
    )
    db.session.add(exercise_set)
    db.session.commit()
    return jsonify(exercise_set.to_dict()), 201
