import logging
from datetime import datetime

from sqlalchemy import func

from app.extensions import db
from app.models.exercise import Exercise
from app.models.exercise_type import ExerciseType
from app.models.workout import Workout
from app.services.errors import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


def _parse_iso(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError) as exc:
        raise ValidationError(
            "performed_at must be ISO 8601", field="performed_at"
        ) from exc


def list_workouts(user_id: int) -> list[Workout]:
    logger.info("Listing workouts for user_id=%s", user_id)
    return (
        Workout.query.filter(Workout.user_id == user_id)
        .order_by(Workout.created_at.desc())
        .all()
    )


def get_workout(workout_id: int, user_id: int) -> Workout:
    """Fetch a workout *owned by* user_id. Cross-user access returns 404
    (not 403) so we don't reveal that the resource exists at all."""
    logger.debug("Fetching workout id=%s for user_id=%s", workout_id, user_id)
    workout = (
        Workout.query.filter(Workout.id == workout_id, Workout.user_id == user_id)
        .first()
    )
    if workout is None:
        logger.warning("Workout id=%s not found for user_id=%s", workout_id, user_id)
        raise NotFoundError(f"Workout {workout_id} not found")
    return workout


def create_workout(data: dict, user_id: int) -> Workout:
    workout = Workout(
        user_id=user_id,
        name=data.get("name"),
        performed_at=_parse_iso(data.get("performed_at")),
        notes=data.get("notes"),
    )
    db.session.add(workout)
    db.session.commit()
    logger.info(
        "Created workout id=%s for user_id=%s name=%r",
        workout.id, user_id, workout.name,
    )
    return workout


def update_workout(workout_id: int, data: dict, user_id: int) -> Workout:
    workout = get_workout(workout_id, user_id)

    if "name" in data:
        workout.name = data["name"]
    if "notes" in data:
        workout.notes = data["notes"]
    if "performed_at" in data:
        workout.performed_at = _parse_iso(data["performed_at"])

    db.session.commit()
    logger.info("Updated workout id=%s fields=%s", workout_id, list(data.keys()))
    return workout


def delete_workout(workout_id: int, user_id: int) -> None:
    workout = get_workout(workout_id, user_id)
    db.session.delete(workout)
    db.session.commit()
    logger.info("Deleted workout id=%s", workout_id)


def add_exercise(workout_id: int, data: dict, user_id: int) -> Exercise:
    get_workout(workout_id, user_id)  # ownership + existence check

    exercise_type_id = data.get("exercise_type_id")
    if not exercise_type_id:
        raise ValidationError(
            "exercise_type_id is required", field="exercise_type_id"
        )

    # ExerciseType is global — no user filter.
    if not db.session.get(ExerciseType, exercise_type_id):
        raise NotFoundError(f"ExerciseType {exercise_type_id} not found")

    if "order" in data:
        order = data["order"]
    else:
        max_order = (
            db.session.query(func.max(Exercise.order))
            .filter(Exercise.workout_id == workout_id)
            .scalar()
        )
        order = (max_order or 0) + 1

    exercise = Exercise(
        workout_id=workout_id,
        exercise_type_id=exercise_type_id,
        order=order,
    )
    db.session.add(exercise)
    db.session.commit()
    logger.info(
        "Added exercise id=%s to workout id=%s (type=%s, order=%s)",
        exercise.id, workout_id, exercise_type_id, exercise.order,
    )
    return exercise
