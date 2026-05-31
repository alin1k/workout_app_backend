import logging

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.exercise import Exercise
from app.models.exercise_type import ExerciseType
from app.services.errors import ConflictError, NotFoundError

logger = logging.getLogger(__name__)


def list_exercise_types() -> list[ExerciseType]:
    logger.info("Listing exercise types")
    return ExerciseType.query.order_by(ExerciseType.name.asc()).all()


def get_exercise_type(et_id: int) -> ExerciseType:
    logger.debug("Fetching exercise type id=%s", et_id)
    et = db.session.get(ExerciseType, et_id)
    if not et:
        logger.warning("ExerciseType id=%s not found", et_id)
        raise NotFoundError(f"ExerciseType {et_id} not found")
    return et


def create_exercise_type(data: dict) -> ExerciseType:
    et = ExerciseType(
        name=data.get("name"),
        description=data.get("description"),
        muscle_group=data.get("muscle_group"),
    )
    db.session.add(et)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        logger.warning("ExerciseType name=%r already exists", data.get("name"))
        raise ConflictError("exercise type with this name already exists") from exc
    logger.info("Created exercise type id=%s name=%r", et.id, et.name)
    return et


def update_exercise_type(et_id: int, data: dict) -> ExerciseType:
    et = get_exercise_type(et_id)

    if "name" in data:
        et.name = data["name"]
    if "description" in data:
        et.description = data["description"]
    if "muscle_group" in data:
        et.muscle_group = data["muscle_group"]

    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError("exercise type with this name already exists") from exc
    logger.info("Updated exercise type id=%s fields=%s", et_id, list(data.keys()))
    return et


def delete_exercise_type(et_id: int) -> None:
    et = get_exercise_type(et_id)

    in_use = db.session.query(Exercise.id).filter(Exercise.exercise_type_id == et_id).first()
    if in_use:
        logger.warning("Cannot delete exercise type id=%s — in use", et_id)
        raise ConflictError("exercise type is in use")

    db.session.delete(et)
    db.session.commit()
    logger.info("Deleted exercise type id=%s", et_id)
