from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.services import dashboard_service

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


def _user_id() -> int:
    return int(get_jwt_identity())


@dashboard_bp.get("/summary")
@jwt_required()
def summary():
    return jsonify(dashboard_service.get_summary(_user_id()))


@dashboard_bp.get("/progress/<int:exercise_type_id>")
@jwt_required()
def progress(exercise_type_id: int):
    return jsonify(dashboard_service.get_progress(exercise_type_id, _user_id()))
