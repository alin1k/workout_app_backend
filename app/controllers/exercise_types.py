from flask import Blueprint, jsonify, request

from app import store
from app.schemas import exercise_type_to_dict

exercise_types_bp = Blueprint("exercise_types", __name__, url_prefix="/api/exercise-types")


@exercise_types_bp.get("")
def list_exercise_types():
    return jsonify([exercise_type_to_dict(et) for et in store.exercise_types.values()])


@exercise_types_bp.post("")
def create_exercise_type():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    if not name:
        return jsonify({"error": "name is required"}), 400
    if any(et["name"].lower() == name.lower() for et in store.exercise_types.values()):
        return jsonify({"error": "exercise type with this name already exists"}), 409

    et = {
        "id": store.next_exercise_type_id(),
        "name": name,
        "description": data.get("description"),
        "muscle_group": data.get("muscle_group"),
    }
    store.exercise_types[et["id"]] = et
    return jsonify(exercise_type_to_dict(et)), 201


@exercise_types_bp.get("/<int:et_id>")
def get_exercise_type(et_id: int):
    et = store.exercise_types.get(et_id)
    if not et:
        return jsonify({"error": "exercise type not found"}), 404
    return jsonify(exercise_type_to_dict(et))


@exercise_types_bp.put("/<int:et_id>")
def update_exercise_type(et_id: int):
    et = store.exercise_types.get(et_id)
    if not et:
        return jsonify({"error": "exercise type not found"}), 404

    data = request.get_json(silent=True) or {}
    for field in ("name", "description", "muscle_group"):
        if field in data:
            et[field] = data[field]
    return jsonify(exercise_type_to_dict(et))


@exercise_types_bp.delete("/<int:et_id>")
def delete_exercise_type(et_id: int):
    if et_id not in store.exercise_types:
        return jsonify({"error": "exercise type not found"}), 404
    if any(e["exercise_type_id"] == et_id for e in store.exercises.values()):
        return jsonify({"error": "exercise type is in use"}), 409
    store.exercise_types.pop(et_id, None)
    return "", 204
