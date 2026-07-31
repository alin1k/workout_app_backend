from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.api_version import API_PREFIX
from app.services import dashboard_service
from app.services.errors import ValidationError

dashboard_bp = Blueprint("dashboard", __name__, url_prefix=f"{API_PREFIX}/dashboard")


def _user_id() -> int:
    return int(get_jwt_identity())


@dashboard_bp.get("/summary")
@jwt_required()
def summary():
    return jsonify(dashboard_service.get_summary(_user_id()))


@dashboard_bp.get("/progress/<int:exercise_type_id>")
@jwt_required()
def progress(exercise_type_id: int):
    return jsonify(
        dashboard_service.get_progress(
            exercise_type_id, _user_id(), _exclude_workout_id()
        )
    )


def _exclude_workout_id() -> int | None:
    """Workout to leave out of `last_session` (the one being logged right now)."""
    raw = request.args.get("exclude_workout_id")
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (ValueError, TypeError) as exc:
        raise ValidationError(
            "exclude_workout_id must be an integer", field="exclude_workout_id"
        ) from exc
