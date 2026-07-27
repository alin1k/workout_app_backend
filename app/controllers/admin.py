from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.api_version import API_PREFIX
from app.controllers.guards import admin_required
from app.pagination import paginated_response, parse_pagination
from app.services import admin_service

admin_bp = Blueprint("admin", __name__, url_prefix=f"{API_PREFIX}/admin")


# Read-only by design. There is no PATCH/DELETE on users, which structurally
# rules out an admin demoting or deleting themselves into a locked-out state.
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
