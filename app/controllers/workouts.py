from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from app.extensions import db
from app.models.exercise import Exercise
from app.models.exercise_type import ExerciseType
from app.models.workout import Workout

workouts_bp = Blueprint("workouts", __name__, url_prefix="/api/workouts")


def _parse_iso(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return ValueError


@workouts_bp.get("")
def list_workouts():
    workouts = Workout.query.order_by(Workout.created_at.desc()).all()
    return jsonify([w.to_dict(include_exercises=False) for w in workouts])


@workouts_bp.post("")
def create_workout():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    if not name:
        return jsonify({"error": "name is required"}), 400

    performed_at = _parse_iso(data.get("performed_at"))
    if performed_at is ValueError:
        return jsonify({"error": "performed_at must be ISO 8601"}), 400

    workout = Workout(
        name=name,
        performed_at=performed_at,
        notes=data.get("notes"),
    )
    db.session.add(workout)
    db.session.commit()
    return jsonify(workout.to_dict()), 201


@workouts_bp.get("/<int:workout_id>")
def get_workout(workout_id: int):
    workout = db.session.get(Workout, workout_id)
    if not workout:
        return jsonify({"error": "workout not found"}), 404
    return jsonify(workout.to_dict())


@workouts_bp.put("/<int:workout_id>")
def update_workout(workout_id: int):
    workout = db.session.get(Workout, workout_id)
    if not workout:
        return jsonify({"error": "workout not found"}), 404

    data = request.get_json(silent=True) or {}
    if "name" in data:
        if not data["name"]:
            return jsonify({"error": "name cannot be empty"}), 400
        workout.name = data["name"]
    if "notes" in data:
        workout.notes = data["notes"]
    if "performed_at" in data:
        performed_at = _parse_iso(data["performed_at"])
        if performed_at is ValueError:
            return jsonify({"error": "performed_at must be ISO 8601"}), 400
        workout.performed_at = performed_at

    db.session.commit()
    return jsonify(workout.to_dict())


@workouts_bp.delete("/<int:workout_id>")
def delete_workout(workout_id: int):
    workout = db.session.get(Workout, workout_id)
    if not workout:
        return jsonify({"error": "workout not found"}), 404
    db.session.delete(workout)
    db.session.commit()
    return "", 204


@workouts_bp.post("/<int:workout_id>/exercises")
def add_exercise(workout_id: int):
    workout = db.session.get(Workout, workout_id)
    if not workout:
        return jsonify({"error": "workout not found"}), 404

    data = request.get_json(silent=True) or {}
    exercise_type_id = data.get("exercise_type_id")
    if not exercise_type_id:
        return jsonify({"error": "exercise_type_id is required"}), 400

    exercise_type = db.session.get(ExerciseType, exercise_type_id)
    if not exercise_type:
        return jsonify({"error": "exercise type not found"}), 404

    if "order" in data:
        order = int(data["order"])
    else:
        max_order = (
            db.session.query(func.max(Exercise.order))
            .filter(Exercise.workout_id == workout_id)
            .scalar()
        )
        order = (max_order or 0) + 1

    exercise = Exercise(
        workout_id=workout_id,
        exercise_type_id=exercise_type_id,
        order=order,
    )
    db.session.add(exercise)
    db.session.commit()
    return jsonify(exercise.to_dict()), 201
