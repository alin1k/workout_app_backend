from flask import Blueprint, jsonify, request

from app.services import workout_service

workouts_bp = Blueprint("workouts", __name__, url_prefix="/api/workouts")


@workouts_bp.get("")
def list_workouts():
    workouts = workout_service.list_workouts()
    return jsonify([w.to_dict(include_exercises=False) for w in workouts])


@workouts_bp.post("")
def create_workout():
    data = request.get_json(silent=True) or {}
    workout = workout_service.create_workout(data)
    return jsonify(workout.to_dict()), 201


@workouts_bp.get("/<int:workout_id>")
def get_workout(workout_id: int):
    workout = workout_service.get_workout(workout_id)
    return jsonify(workout.to_dict())


@workouts_bp.put("/<int:workout_id>")
def update_workout(workout_id: int):
    data = request.get_json(silent=True) or {}
    workout = workout_service.update_workout(workout_id, data)
    return jsonify(workout.to_dict())


@workouts_bp.delete("/<int:workout_id>")
def delete_workout(workout_id: int):
    workout_service.delete_workout(workout_id)
    return "", 204


@workouts_bp.post("/<int:workout_id>/exercises")
def add_exercise(workout_id: int):
    data = request.get_json(silent=True) or {}
    exercise = workout_service.add_exercise(workout_id, data)
    return jsonify(exercise.to_dict()), 201
