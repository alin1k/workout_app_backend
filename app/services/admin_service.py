"""Admin-only queries and account creation.

Unlike the other services this one returns plain dicts rather than model
instances: a row here is a projection (a User plus two aggregates), not a
persistable entity, and assembling it in the controller would leak the
tuple shape upward.
"""

import logging

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.user import User
from app.models.workout import Workout
from app.services.errors import ConflictError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)


def _escape_like(value: str) -> str:
    """Escape LIKE wildcards so user input matches literally."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _apply_q(query, q: str | None):
    if q and q.strip():
        pattern = f"%{_escape_like(q.strip())}%"
        return query.filter(User.username.ilike(pattern, escape="\\"))
    return query


def _stats_query():
    """Users left-joined to their workout aggregates.

    One round trip for every user plus their derived stats. count() over
    Workout.id skips NULLs, so a user with no workouts correctly comes back
    as 0 rather than 1. LIMIT/OFFSET applied on top of the GROUP BY
    paginates users (one row per group), which is what makes this shape
    safe for a paged listing.
    """
    return (
        db.session.query(
            User,
            func.count(Workout.id).label("workout_count"),
            # coalesce per row, then MAX — a workout with no performed_at
            # falls back to when it was created.
            func.max(
                func.coalesce(Workout.performed_at, Workout.created_at)
            ).label("last_activity"),
        )
        .outerjoin(Workout, Workout.user_id == User.id)
        .group_by(User.id)
    )


def _serialize(user: User, workout_count, last_activity) -> dict:
    return {
        **user.to_dict(),
        "workout_count": int(workout_count or 0),
        "last_activity": last_activity.isoformat() if last_activity else None,
    }


def list_users(
    limit: int, offset: int, q: str | None = None
) -> tuple[list[dict], int]:
    logger.info("Admin listing users limit=%s offset=%s q=%r", limit, offset, q)

    rows = (
        _apply_q(_stats_query(), q)
        .order_by(User.id.asc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    # Count users, not groups. `.count()` on the grouped query would wrap the
    # whole aggregate in a subquery; a scalar count over the same filter is
    # cheaper and reads better.
    total = _apply_q(db.session.query(func.count(User.id)), q).scalar() or 0

    return [_serialize(user, count, last) for user, count, last in rows], total


def get_user(user_id: int) -> dict:
    row = _stats_query().filter(User.id == user_id).first()
    if row is None:
        logger.warning("Admin lookup: user id=%s not found", user_id)
        raise NotFoundError(f"User {user_id} not found")
    return _serialize(*row)


def create_user(data: dict, *, is_admin: bool = False, created_by=None) -> dict:
    """Create an account on someone's behalf.

    This is the only way accounts come into existence — there is no
    self-registration. `is_admin` is a keyword the caller sets, never a
    payload field: the HTTP endpoint leaves it False so the app can only
    mint normal users, and the `create-admin` CLI command passes True.
    """
    username = data.get("username")
    password = data.get("password")

    if not isinstance(password, str) or password == "":
        raise ValidationError("password is required", field="password")

    # Model-level validation (username length, password min length) raises
    # ValidationError.
    user = User(username=username, is_admin=is_admin)
    user.set_password(password)

    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        logger.warning("Account creation rejected: username=%r already taken", username)
        # Unlike login, the caller is a trusted admin — say what went wrong.
        raise ConflictError("username is already taken")

    logger.info(
        "Created user id=%s username=%r is_admin=%s created_by=%s",
        user.id,
        user.username,
        user.is_admin,
        created_by,
    )
    return _serialize(user, 0, None)
