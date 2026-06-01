import logging

from sqlalchemy import func

from app.extensions import db
from app.models.exercise import Exercise
from app.models.exercise_set import ExerciseSet
from app.models.workout import Workout
from app.services.errors import NotFoundError, ValidationError

logger = logging.getLogger(__name__)

# Fields the client is allowed to mutate via PUT /api/sets/<id>.
_MUTABLE_SET_FIELDS = ("reps", "weight")

# Fields the client is allowed to mutate via PUT /api/exercises/<id>.
_MUTABLE_EXERCISE_FIELDS = ("order",)


def get_exercise(exercise_id: int, user_id: int) -> Exercise:
    """Fetch an exercise *whose workout belongs to* user_id."""
    logger.debug("Fetching exercise id=%s for user_id=%s", exercise_id, user_id)
    exercise = (
        db.session.query(Exercise)
        .join(Workout)
        .filter(Exercise.id == exercise_id, Workout.user_id == user_id)
        .first()
    )
    if exercise is None:
        logger.warning(
            "Exercise id=%s not found for user_id=%s", exercise_id, user_id
        )
        raise NotFoundError(f"Exercise {exercise_id} not found")
    return exercise


def delete_exercise(exercise_id: int, user_id: int) -> None:
    exercise = get_exercise(exercise_id, user_id)
    db.session.delete(exercise)
    db.session.commit()
    logger.info("Deleted exercise id=%s", exercise_id)


def update_exercise(exercise_id: int, data: dict, user_id: int):
    """Update an exercise. Today the only mutable field is `order`; changing
    it moves the exercise to that position and re-numbers the others 1..N.
    Returns the parent Workout so the caller can serialize the full nested tree.
    """
    exercise = get_exercise(exercise_id, user_id)

    provided = [f for f in _MUTABLE_EXERCISE_FIELDS if f in data]
    if not provided:
        raise ValidationError("no fields to update")

    if "order" in data:
        _move_exercise(exercise, data["order"])

    db.session.commit()
    return exercise.workout


def _move_exercise(exercise: Exercise, target_order) -> None:
    """In-place reorder; no commit here — the caller owns the transaction."""
    if target_order is None:
        raise ValidationError("order is required", field="order")
    try:
        target = int(target_order)
    except (TypeError, ValueError) as exc:
        raise ValidationError("order must be an integer", field="order") from exc
    if target < 1:
        raise ValidationError("order must be positive", field="order")

    siblings = (
        db.session.query(Exercise)
        .filter(Exercise.workout_id == exercise.workout_id)
        .order_by(Exercise.order)
        .all()
    )
    siblings.remove(exercise)

    insert_pos = min(target, len(siblings) + 1)
    siblings.insert(insert_pos - 1, exercise)

    for new_order, sib in enumerate(siblings, start=1):
        sib.order = new_order

    logger.info(
        "Moved exercise id=%s in workout id=%s to order=%s (requested=%s)",
        exercise.id, exercise.workout_id, insert_pos, target,
    )


def add_set(exercise_id: int, data: dict, user_id: int) -> ExerciseSet:
    get_exercise(exercise_id, user_id)  # ownership + existence

    if "set_number" in data:
        set_number = data["set_number"]
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
        reps=data.get("reps"),
        weight=data.get("weight"),
    )
    db.session.add(exercise_set)
    db.session.commit()
    logger.info(
        "Added set id=%s to exercise id=%s (#%s, %s reps, %s kg)",
        exercise_set.id, exercise_id, exercise_set.set_number,
        exercise_set.reps, exercise_set.weight,
    )
    return exercise_set


def get_set(set_id: int, user_id: int) -> ExerciseSet:
    """Fetch a set whose owning workout belongs to user_id."""
    logger.debug("Fetching set id=%s for user_id=%s", set_id, user_id)
    exercise_set = (
        db.session.query(ExerciseSet)
        .join(Exercise)
        .join(Workout)
        .filter(ExerciseSet.id == set_id, Workout.user_id == user_id)
        .first()
    )
    if exercise_set is None:
        logger.warning("Set id=%s not found for user_id=%s", set_id, user_id)
        raise NotFoundError(f"Set {set_id} not found")
    return exercise_set


def delete_set(set_id: int, user_id: int) -> None:
    exercise_set = get_set(set_id, user_id)
    db.session.delete(exercise_set)
    db.session.commit()
    logger.info("Deleted set id=%s", set_id)


def update_set(set_id: int, data: dict, user_id: int) -> ExerciseSet:
    exercise_set = get_set(set_id, user_id)

    provided = [f for f in _MUTABLE_SET_FIELDS if f in data]
    if not provided:
        raise ValidationError("no fields to update")

    if "reps" in data:
        exercise_set.reps = data["reps"]
    if "weight" in data:
        exercise_set.weight = data["weight"]

    db.session.commit()
    logger.info("Updated set id=%s fields=%s", set_id, provided)
    return exercise_set
