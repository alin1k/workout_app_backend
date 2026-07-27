from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.api_version import API_PREFIX
from app.controllers.guards import admin_required
from app.pagination import paginated_response, parse_pagination
from app.services import exercise_type_service

exercise_types_bp = Blueprint(
    "exercise_types", __name__, url_prefix=f"{API_PREFIX}/exercise-types"
)


@exercise_types_bp.get("")
@jwt_required()
def list_exercise_types():
    pagination = parse_pagination(request.args)
    items, total = exercise_type_service.list_exercise_types(
        pagination.limit,
        pagination.offset,
        q=request.args.get("q"),
        muscle_group=request.args.get("muscle_group"),
    )
    return jsonify(
        paginated_response([et.to_dict() for et in items], total, pagination)
    )


@exercise_types_bp.get("/muscle-groups")
@jwt_required()
def list_muscle_groups():
    return jsonify({"data": exercise_type_service.list_muscle_groups()})


# Deliberately NOT admin-gated: this powers the inline "add new movement"
# flow in the exercise picker. Adding to the catalog is additive; editing
# and deleting mutate what everyone else already logged, so those are.
@exercise_types_bp.post("")
@jwt_required()
def create_exercise_type():
    data = request.get_json(silent=True) or {}
    et = exercise_type_service.create_exercise_type(data)
    return jsonify(et.to_dict()), 201


@exercise_types_bp.get("/<int:et_id>")
@jwt_required()
def get_exercise_type(et_id: int):
    et = exercise_type_service.get_exercise_type(et_id)
    return jsonify(et.to_dict())


@exercise_types_bp.patch("/<int:et_id>")
@jwt_required()
@admin_required
def update_exercise_type(et_id: int):
    data = request.get_json(silent=True) or {}
    et = exercise_type_service.update_exercise_type(et_id, data)
    return jsonify(et.to_dict())


@exercise_types_bp.delete("/<int:et_id>")
@jwt_required()
@admin_required
def delete_exercise_type(et_id: int):
    exercise_type_service.delete_exercise_type(et_id)
    return "", 204
