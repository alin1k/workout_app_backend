from itertools import count

workouts: dict[int, dict] = {}
exercise_types: dict[int, dict] = {}
exercises: dict[int, dict] = {}
sets: dict[int, dict] = {}

_workout_ids = count(1)
_exercise_type_ids = count(1)
_exercise_ids = count(1)
_set_ids = count(1)


def next_workout_id() -> int:
    return next(_workout_ids)


def next_exercise_type_id() -> int:
    return next(_exercise_type_ids)


def next_exercise_id() -> int:
    return next(_exercise_ids)


def next_set_id() -> int:
    return next(_set_ids)
