from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.api_version import API_PREFIX
from app.controllers.guards import admin_required
from app.pagination import paginated_response, parse_pagination
from app.services import admin_service

admin_bp = Blueprint("admin", __name__, url_prefix=f"{API_PREFIX}/admin")


# List, read and create only. There is no PATCH/DELETE on users, which
# structurally rules out an admin demoting or deleting themselves into a
# locked-out state.
@admin_bp.get("/users")
@jwt_required()
@admin_required
def list_users():
    pagination = parse_pagination(request.args)
    items, total = admin_service.list_users(
        pagination.limit,
        pagination.offset,
        q=request.args.get("q"),
    )
    return jsonify(paginated_response(items, total, pagination))


@admin_bp.get("/users/<int:user_id>")
@jwt_required()
@admin_required
def get_user(user_id: int):
    return jsonify(admin_service.get_user(user_id))


# The only way to create an account. Always a normal user: `is_admin` in the
# body is ignored, and no token is issued — the admin stays signed in as
# themselves and hands the credentials over out of band.
@admin_bp.post("/users")
@jwt_required()
@admin_required
def create_user():
    data = request.get_json(silent=True) or {}
    user = admin_service.create_user(data, created_by=get_jwt_identity())
    return jsonify(user), 201
