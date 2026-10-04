"""Dev-only seed data: two known logins, a movement catalogue and a few weeks
of workout history for each user.

Runs automatically on `docker compose up` (see docker-compose.override.yml).
To run it by hand against the running dev container:

    docker exec workout_app_web python -m scripts.seed_dev           # fill in what's missing
    docker exec workout_app_web python -m scripts.seed_dev --reset   # wipe the seed users' workouts and re-create them

Idempotent. Each run:
  * creates the seed users if missing and puts their password / admin flag
    back to the values below;
  * creates any missing movements (matched by name);
  * adds the workout history only to a seed user who has no workouts at all,
    so anything you log yourself is left alone.

NEVER for production. Three things keep it out:
  1. only docker-compose.override.yml calls it, and prod passes explicit -f
     files, which skips the override;
  2. scripts/ is in .dockerignore, so the file isn't in the image — the dev
     override bind-mounts it;
  3. the FLASK_ENV check below refuses to run anywhere else.
"""
import os
import sys
from datetime import datetime, timedelta, timezone

if os.environ.get("FLASK_ENV") != "development":
    sys.exit("seed_dev: refusing to run — FLASK_ENV is not 'development'")

from werkzeug.security import generate_password_hash  # noqa: E402

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Exercise, ExerciseSet, ExerciseType, User, Workout  # noqa: E402

# (name, muscle_group, description)
MOVEMENTS = [
    ("Bench Press", "chest", "Barbell press from a flat bench."),
    ("Incline Dumbbell Press", "chest", "Dumbbell press on a 30–45° incline."),
    ("Overhead Press", "shoulders", "Standing barbell press from the shoulders."),
    ("Lateral Raise", "shoulders", "Dumbbell raise out to the sides."),
    ("Triceps Pushdown", "arms", "Cable pushdown with a rope or bar."),
    ("Barbell Curl", "arms", "Standing curl with a straight or EZ bar."),
    ("Deadlift", "back", "Conventional barbell deadlift from the floor."),
    ("Barbell Row", "back", "Bent-over row, bar pulled to the lower ribs."),
    ("Lat Pulldown", "back", "Cable pulldown to the upper chest."),
    ("Pull-Up", "back", "Bodyweight pull-up, overhand grip."),
    ("Squat", "legs", "Barbell back squat."),
    ("Romanian Deadlift", "legs", "Hip hinge with a slight knee bend."),
    ("Leg Press", "legs", "Machine leg press."),
    ("Calf Raise", "legs", "Standing or machine calf raise."),
    ("Hanging Leg Raise", "core", "Leg raise hanging from a bar."),
]

# Each template line: (movement, starting weight in kg or None for bodyweight,
# kg added every time the template comes round again, reps per set).
# Each schedule line: (days ago, template name, notes).
USERS = [
    {
        "username": "admin",
        "password": "admin",
        "is_admin": True,
        "templates": {
            "Push day": [
                ("Bench Press", 70, 2.5, [8, 8, 6]),
                ("Overhead Press", 40, 2.5, [8, 7, 6]),
                ("Incline Dumbbell Press", 24, 2, [10, 10, 8]),
                ("Lateral Raise", 8, 1, [15, 12, 12]),
                ("Triceps Pushdown", 25, 2.5, [12, 12, 10]),
            ],
            "Pull day": [
                ("Deadlift", 110, 5, [5, 5, 5]),
                ("Pull-Up", None, 0, [8, 7, 6]),
                ("Barbell Row", 60, 2.5, [8, 8, 8]),
                ("Lat Pulldown", 55, 2.5, [10, 10, 9]),
                ("Barbell Curl", 30, 2.5, [10, 9, 8]),
            ],
            "Leg day": [
                ("Squat", 90, 5, [6, 6, 5]),
                ("Romanian Deadlift", 80, 5, [8, 8, 8]),
                ("Leg Press", 140, 10, [10, 10, 10]),
                ("Calf Raise", 60, 5, [15, 15, 12]),
                ("Hanging Leg Raise", None, 0, [12, 10, 10]),
            ],
        },
        "schedule": [
            (22, "Push day", None),
            (20, "Pull day", None),
            (18, "Leg day", "Knees felt good, depth was solid."),
            (15, "Push day", None),
            (13, "Pull day", "Grip gave out on the last deadlift set."),
            (11, "Leg day", None),
            (8, "Push day", None),
            (6, "Pull day", None),
            (4, "Leg day", None),
            (1, "Push day", "Bench moved fast — go up next week."),
        ],
    },
    {
        "username": "demo",
        "password": "demo",
        "is_admin": False,
        "templates": {
            "Upper body": [
                ("Bench Press", 40, 2.5, [10, 10, 8]),
                ("Lat Pulldown", 35, 2.5, [12, 10, 10]),
                ("Overhead Press", 22.5, 2.5, [10, 8, 8]),
                ("Barbell Curl", 17.5, 2.5, [12, 12, 10]),
            ],
            "Lower body": [
                ("Squat", 50, 5, [8, 8, 8]),
                ("Romanian Deadlift", 45, 5, [10, 10, 10]),
                ("Leg Press", 80, 10, [12, 12, 10]),
                ("Hanging Leg Raise", None, 0, [10, 8, 8]),
            ],
        },
        "schedule": [
            (19, "Upper body", "First session back."),
            (16, "Lower body", None),
            (12, "Upper body", None),
            (9, "Lower body", None),
            (5, "Upper body", None),
            (2, "Lower body", "Squats finally feel stable."),
        ],
    },
]


def seed_movements() -> dict[str, ExerciseType]:
    by_name = {t.name: t for t in ExerciseType.query.all()}
    created = 0
    for name, muscle_group, description in MOVEMENTS:
        if name not in by_name:
            by_name[name] = ExerciseType(
                name=name, muscle_group=muscle_group, description=description
            )
            db.session.add(by_name[name])
            created += 1
    db.session.flush()
    print(f"seed_dev: movements — {created} created, {len(MOVEMENTS) - created} already there")
    return by_name


def seed_user(spec: dict) -> User:
    user = User.query.filter(User.username == spec["username"]).first()
    created = user is None
    if created:
        user = User(username=spec["username"])
        db.session.add(user)
    # Hash directly instead of User.set_password(): these throwaway dev
    # passwords are shorter than the 8-character minimum it enforces.
    if created or not user.check_password(spec["password"]):
        user.password_hash = generate_password_hash(spec["password"])
    user.is_admin = spec["is_admin"]
    db.session.flush()
    print(
        f"seed_dev: user {user.username!r} — {'created' if created else 'already there'}"
        f" (is_admin={user.is_admin})"
    )
    return user


def seed_workouts(user: User, spec: dict, movements: dict[str, ExerciseType], reset: bool) -> None:
    existing = Workout.query.filter(Workout.user_id == user.id).all()
    if existing and not reset:
        print(f"seed_dev: workouts for {user.username!r} — skipped, already has {len(existing)}")
        return
    for workout in existing:
        db.session.delete(workout)

    # Early-evening sessions; schedule days are all >= 1 so none land in the future.
    today = datetime.now(timezone.utc).replace(hour=17, minute=30, second=0, microsecond=0)
    seen: dict[str, int] = {}
    for days_ago, template, notes in sorted(spec["schedule"], reverse=True):
        round_no = seen.get(template, 0)
        seen[template] = round_no + 1
        workout = Workout(
            user_id=user.id,
            name=template,
            notes=notes,
            performed_at=today - timedelta(days=days_ago),
        )
        for order, (movement, start, step, reps) in enumerate(spec["templates"][template], 1):
            exercise = Exercise(exercise_type=movements[movement], order=order)
            weight = None if start is None else start + step * round_no
            for set_number, rep_count in enumerate(reps, 1):
                # Bodyweight movements progress by a rep per round instead of by load.
                rep_count += round_no if start is None else 0
                exercise.sets.append(
                    ExerciseSet(set_number=set_number, reps=rep_count, weight=weight)
                )
            workout.exercises.append(exercise)
        db.session.add(workout)
    verb = "re-created" if existing else "created"
    print(f"seed_dev: workouts for {user.username!r} — {len(spec['schedule'])} {verb}")


def main() -> None:
    reset = "--reset" in sys.argv[1:]
    app = create_app()
    with app.app_context():
        movements = seed_movements()
        for spec in USERS:
            user = seed_user(spec)
            seed_workouts(user, spec, movements, reset)
        db.session.commit()


if __name__ == "__main__":
    main()
