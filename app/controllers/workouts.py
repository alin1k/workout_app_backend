from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from app import store
from app.schemas import exercise_to_dict, workout_to_dict

workouts_bp = Blueprint("workouts", __name__, url_prefix="/api/workouts")


@workouts_bp.get("")
def list_workouts():
    items = [workout_to_dict(w, include_exercises=False) for w in store.workouts.values()]
    return jsonify(items)


@workouts_bp.post("")
def create_workout():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    if not name:
        return jsonify({"error": "name is required"}), 400

    workout = {
        "id": store.next_workout_id(),
        "name": name,
        "performed_at": data.get("performed_at"),
        "notes": data.get("notes"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    store.workouts[workout["id"]] = workout
    return jsonify(workout_to_dict(workout)), 201


@workouts_bp.get("/<int:workout_id>")
def get_workout(workout_id: int):
    workout = store.workouts.get(workout_id)
    if not workout:
        return jsonify({"error": "workout not found"}), 404
    return jsonify(workout_to_dict(workout))


@workouts_bp.put("/<int:workout_id>")
def update_workout(workout_id: int):
    workout = store.workouts.get(workout_id)
    if not workout:
        return jsonify({"error": "workout not found"}), 404

    data = request.get_json(silent=True) or {}
    for field in ("name", "performed_at", "notes"):
        if field in data:
            workout[field] = data[field]
    return jsonify(workout_to_dict(workout))


@workouts_bp.delete("/<int:workout_id>")
def delete_workout(workout_id: int):
    if workout_id not in store.workouts:
        return jsonify({"error": "workout not found"}), 404

    exercise_ids = [e["id"] for e in store.exercises.values() if e["workout_id"] == workout_id]
    for eid in exercise_ids:
        set_ids = [s["id"] for s in store.sets.values() if s["exercise_id"] == eid]
        for sid in set_ids:
            store.sets.pop(sid, None)
        store.exercises.pop(eid, None)
    store.workouts.pop(workout_id, None)
    return "", 204


@workouts_bp.post("/<int:workout_id>/exercises")
def add_exercise(workout_id: int):
    if workout_id not in store.workouts:
        return jsonify({"error": "workout not found"}), 404

    data = request.get_json(silent=True) or {}
    exercise_type_id = data.get("exercise_type_id")
    if not exercise_type_id:
        return jsonify({"error": "exercise_type_id is required"}), 400
    if exercise_type_id not in store.exercise_types:
        return jsonify({"error": "exercise type not found"}), 404

    existing_orders = [
        e["order"] for e in store.exercises.values() if e["workout_id"] == workout_id
    ]
    default_order = (max(existing_orders) + 1) if existing_orders else 1

    exercise = {
        "id": store.next_exercise_id(),
        "workout_id": workout_id,
        "exercise_type_id": exercise_type_id,
        "order": int(data.get("order", default_order)),
    }
    store.exercises[exercise["id"]] = exercise
    return jsonify(exercise_to_dict(exercise)), 201
