from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.exercise import Exercise
from app.models.exercise_type import ExerciseType

exercise_types_bp = Blueprint("exercise_types", __name__, url_prefix="/api/exercise-types")


@exercise_types_bp.get("")
def list_exercise_types():
    items = ExerciseType.query.order_by(ExerciseType.name.asc()).all()
    return jsonify([et.to_dict() for et in items])


@exercise_types_bp.post("")
def create_exercise_type():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    if not name:
        return jsonify({"error": "name is required"}), 400

    et = ExerciseType(
        name=name,
        description=data.get("description"),
        muscle_group=data.get("muscle_group"),
    )
    db.session.add(et)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "exercise type with this name already exists"}), 409
    return jsonify(et.to_dict()), 201


@exercise_types_bp.get("/<int:et_id>")
def get_exercise_type(et_id: int):
    et = db.session.get(ExerciseType, et_id)
    if not et:
        return jsonify({"error": "exercise type not found"}), 404
    return jsonify(et.to_dict())


@exercise_types_bp.put("/<int:et_id>")
def update_exercise_type(et_id: int):
    et = db.session.get(ExerciseType, et_id)
    if not et:
        return jsonify({"error": "exercise type not found"}), 404

    data = request.get_json(silent=True) or {}
    if "name" in data:
        if not data["name"]:
            return jsonify({"error": "name cannot be empty"}), 400
        et.name = data["name"]
    if "description" in data:
        et.description = data["description"]
    if "muscle_group" in data:
        et.muscle_group = data["muscle_group"]

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "exercise type with this name already exists"}), 409
    return jsonify(et.to_dict())


@exercise_types_bp.delete("/<int:et_id>")
def delete_exercise_type(et_id: int):
    et = db.session.get(ExerciseType, et_id)
    if not et:
        return jsonify({"error": "exercise type not found"}), 404

    in_use = db.session.query(Exercise.id).filter(Exercise.exercise_type_id == et_id).first()
    if in_use:
        return jsonify({"error": "exercise type is in use"}), 409

    db.session.delete(et)
    db.session.commit()
    return "", 204
