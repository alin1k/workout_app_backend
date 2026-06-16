import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.exercise import Exercise
from app.models.exercise_type import ExerciseType
from app.models.workout import Workout
from app.services.errors import NotFoundError

logger = logging.getLogger(__name__)


def _effective_date(workout: Workout) -> datetime:
    """A workout's effective date: performed_at, falling back to created_at.

    `performed_at` is nullable and stored values may come back naive depending on
    the driver; treat any naive datetime as UTC so comparisons against an aware
    `now` never raise.
    """
    value = workout.performed_at or workout.created_at
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value


def get_summary(user_id: int) -> dict:
    """This-week stats + the exercise types that have logged sets."""
    logger.info("Building dashboard summary for user_id=%s", user_id)

    workouts = (
        Workout.query.filter(Workout.user_id == user_id)
        .options(
            selectinload(Workout.exercises).selectinload(Exercise.sets),
            selectinload(Workout.exercises).selectinload(Exercise.exercise_type),
        )
        .all()
    )

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=7)

    volume = 0.0
    sessions = 0
    set_count = 0
    type_counts: dict[int, dict] = {}

    for workout in workouts:
        in_window = cutoff <= _effective_date(workout) <= now
        if in_window:
            sessions += 1

        for exercise in workout.exercises:
            sets = exercise.sets
            if sets and exercise.exercise_type is not None:
                entry = type_counts.setdefault(
                    exercise.exercise_type_id,
                    {
                        "id": exercise.exercise_type.id,
                        "name": exercise.exercise_type.name,
                        "muscle_group": exercise.exercise_type.muscle_group,
                        "times_logged": 0,
                    },
                )
                entry["times_logged"] += 1

            if in_window:
                set_count += len(sets)
                for s in sets:
                    if s.weight is not None:
                        volume += s.reps * s.weight

    exercise_types = sorted(
        type_counts.values(), key=lambda t: (-t["times_logged"], t["name"])
    )

    return {
        "week": {
            "volume_kg": round(volume),
            "sessions": sessions,
            "sets": set_count,
        },
        "exercise_types": exercise_types,
    }


def get_progress(exercise_type_id: int, user_id: int) -> dict:
    """Per-workout 'heaviest set' series + PR for one exercise type."""
    logger.info(
        "Building progress for exercise_type_id=%s user_id=%s",
        exercise_type_id, user_id,
    )
    # ExerciseType is global — no user filter (same as workout_service.add_exercise).
    exercise_type = db.session.get(ExerciseType, exercise_type_id)
    if exercise_type is None:
        logger.warning("ExerciseType id=%s not found", exercise_type_id)
        raise NotFoundError("exercise type not found")

    # Only this user's workouts that contain an exercise of this type, sets eager-loaded.
    workouts = (
        Workout.query.join(Exercise, Exercise.workout_id == Workout.id)
        .filter(
            Workout.user_id == user_id,
            Exercise.exercise_type_id == exercise_type_id,
        )
        .options(selectinload(Workout.exercises).selectinload(Exercise.sets))
        .distinct()
        .all()
    )

    # Gather, per workout, every set belonging to an exercise instance of this type
    # (a type appearing as two entries in one workout → sets merged into one point).
    workout_sets: list[tuple[Workout, list]] = []
    for workout in workouts:
        sets = [
            s
            for exercise in workout.exercises
            if exercise.exercise_type_id == exercise_type_id
            for s in exercise.sets
        ]
        if sets:
            workout_sets.append((workout, sets))

    # unit: "kg" if any set of this type across the whole history has a weight.
    unit = "kg" if any(
        s.weight is not None for _, sets in workout_sets for s in sets
    ) else "reps"

    series = []
    for workout, sets in workout_sets:
        if unit == "kg":
            weighted = [s for s in sets if s.weight is not None]
            if not weighted:
                # Only bodyweight sets of a weighted type → skip (never mix units).
                continue
            value = max(s.weight for s in weighted)
            volume = round(sum(s.reps * s.weight for s in weighted))
        else:
            value = max(s.reps for s in sets)
            volume = 0

        series.append({
            "workout_id": workout.id,
            "workout_name": workout.name,
            "date": _effective_date(workout).isoformat(),
            "value": value,
            "sets": len(sets),
            "volume_kg": volume,
            "_sort": (_effective_date(workout), workout.id),
        })

    series.sort(key=lambda p: p.pop("_sort"))

    pr = None
    if series:
        # First workout (in chart order) that achieves the max value.
        best = max(p["value"] for p in series)
        pr_point = next(p for p in series if p["value"] == best)
        pr = {"value": best, "date": pr_point["date"]}

    return {
        "exercise_type": {
            "id": exercise_type.id,
            "name": exercise_type.name,
            "muscle_group": exercise_type.muscle_group,
        },
        "unit": unit,
        "series": series,
        "pr": pr,
    }
