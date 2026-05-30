from app import store


def set_to_dict(s: dict) -> dict:
    return {
        "id": s["id"],
        "exercise_id": s["exercise_id"],
        "set_number": s["set_number"],
        "reps": s["reps"],
        "weight": s["weight"],
    }


def exercise_type_to_dict(et: dict) -> dict:
    return {
        "id": et["id"],
        "name": et["name"],
        "description": et.get("description"),
        "muscle_group": et.get("muscle_group"),
    }


def exercise_to_dict(e: dict, include_sets: bool = True) -> dict:
    et = store.exercise_types.get(e["exercise_type_id"])
    out = {
        "id": e["id"],
        "workout_id": e["workout_id"],
        "exercise_type_id": e["exercise_type_id"],
        "exercise_type": exercise_type_to_dict(et) if et else None,
        "order": e["order"],
    }
    if include_sets:
        out["sets"] = [
            set_to_dict(s)
            for s in sorted(
                (s for s in store.sets.values() if s["exercise_id"] == e["id"]),
                key=lambda s: s["set_number"],
            )
        ]
    return out


def workout_to_dict(w: dict, include_exercises: bool = True) -> dict:
    out = {
        "id": w["id"],
        "name": w["name"],
        "performed_at": w.get("performed_at"),
        "notes": w.get("notes"),
        "created_at": w["created_at"],
    }
    if include_exercises:
        out["exercises"] = [
            exercise_to_dict(e)
            for e in sorted(
                (e for e in store.exercises.values() if e["workout_id"] == w["id"]),
                key=lambda e: e["order"],
            )
        ]
    return out
