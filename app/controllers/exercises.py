from flask import Blueprint, jsonify, request

from app import store
from app.schemas import set_to_dict

exercises_bp = Blueprint("exercises", __name__, url_prefix="/api/exercises")


@exercises_bp.delete("/<int:exercise_id>")
def delete_exercise(exercise_id: int):
    if exercise_id not in store.exercises:
        return jsonify({"error": "exercise not found"}), 404

    set_ids = [s["id"] for s in store.sets.values() if s["exercise_id"] == exercise_id]
    for sid in set_ids:
        store.sets.pop(sid, None)
    store.exercises.pop(exercise_id, None)
    return "", 204


@exercises_bp.post("/<int:exercise_id>/sets")
def add_set(exercise_id: int):
    if exercise_id not in store.exercises:
        return jsonify({"error": "exercise not found"}), 404

    data = request.get_json(silent=True) or {}
    reps = data.get("reps")
    if reps is None:
        return jsonify({"error": "reps is required"}), 400

    existing_set_numbers = [
        s["set_number"] for s in store.sets.values() if s["exercise_id"] == exercise_id
    ]
    default_set_number = (max(existing_set_numbers) + 1) if existing_set_numbers else 1

    s = {
        "id": store.next_set_id(),
        "exercise_id": exercise_id,
        "set_number": int(data.get("set_number", default_set_number)),
        "reps": int(reps),
        "weight": float(data["weight"]) if data.get("weight") is not None else None,
    }
    store.sets[s["id"]] = s
    return jsonify(set_to_dict(s)), 201
