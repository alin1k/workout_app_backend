import logging

from sqlalchemy import func

from app.extensions import db
from app.models.exercise import Exercise
from app.models.exercise_set import ExerciseSet
from app.services.errors import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


def get_exercise(exercise_id: int) -> Exercise:
    logger.debug("Fetching exercise id=%s", exercise_id)
    exercise = db.session.get(Exercise, exercise_id)
    if not exercise:
        logger.warning("Exercise id=%s not found", exercise_id)
        raise NotFoundError(f"Exercise {exercise_id} not found")
    return exercise


def delete_exercise(exercise_id: int) -> None:
    exercise = get_exercise(exercise_id)
    db.session.delete(exercise)
    db.session.commit()
    logger.info("Deleted exercise id=%s", exercise_id)


def add_set(exercise_id: int, data: dict) -> ExerciseSet:
    get_exercise(exercise_id)  # raises NotFoundError if missing

    if data.get("reps") is None:
        raise ValidationError("reps is required", field="reps")

    try:
        reps = int(data["reps"])
    except (TypeError, ValueError) as exc:
        raise ValidationError("reps must be an integer", field="reps") from exc

    weight = data.get("weight")
    if weight is not None:
        try:
            weight = float(weight)
        except (TypeError, ValueError) as exc:
            raise ValidationError("weight must be a number", field="weight") from exc

    if "set_number" in data:
        set_number = int(data["set_number"])
    else:
        max_number = (
            db.session.query(func.max(ExerciseSet.set_number))
            .filter(ExerciseSet.exercise_id == exercise_id)
            .scalar()
        )
        set_number = (max_number or 0) + 1

    exercise_set = ExerciseSet(
        exercise_id=exercise_id,
        set_number=set_number,
        reps=reps,
        weight=weight,
    )
    db.session.add(exercise_set)
    db.session.commit()
    logger.info(
        "Added set id=%s to exercise id=%s (#%s, %s reps, %s kg)",
        exercise_set.id, exercise_id, set_number, reps, weight,
    )
    return exercise_set


def delete_set(set_id: int) -> None:
    exercise_set = db.session.get(ExerciseSet, set_id)
    if not exercise_set:
        logger.warning("Set id=%s not found", set_id)
        raise NotFoundError(f"Set {set_id} not found")
    db.session.delete(exercise_set)
    db.session.commit()
    logger.info("Deleted set id=%s", set_id)
