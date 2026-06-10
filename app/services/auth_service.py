import hmac
import logging

from flask import current_app
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.user import User
from app.services.errors import AuthenticationError, ValidationError

logger = logging.getLogger(__name__)


def _issue_token(user: User) -> str:
    # JWT identity must be a string in flask-jwt-extended 4.x.
    return create_access_token(identity=str(user.id))


def _reject_registration() -> None:
    """Single response for every registration failure that we DON'T want to
    distinguish to the caller: bad key, missing key, locked endpoint, OR
    username already taken. All look identical to the client."""
    raise AuthenticationError("registration is closed")


def register(data: dict, registration_key: str) -> tuple[User, str]:
    expected = current_app.config.get("REGISTRATION_KEY") or ""

    # Lock check: if the server has no key configured, OR the caller sent
    # nothing, OR the values don't match → identical 401 every time.
    if (
        not expected
        or not registration_key
        or not hmac.compare_digest(str(registration_key), str(expected))
    ):
        logger.warning("Registration rejected: invalid or missing key")
        _reject_registration()

    # Past the gate. Now do input shape validation (these CAN surface specific
    # field errors — the caller already proved they hold the key, so revealing
    # 'password must be ≥ 8 chars' isn't leaking anything sensitive).
    username = data.get("username")
    password = data.get("password")

    if password is None or password == "":
        raise ValidationError("password is required", field="password")

    user = User(username=username)
    user.set_password(password)

    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()

        logger.warning("Registration rejected: username=%r already taken", username)
        _reject_registration()

    logger.info("Registered user id=%s username=%r", user.id, user.username)
    return user, _issue_token(user)


def authenticate(data: dict) -> tuple[User, str]:
    username = data.get("username")
    password = data.get("password")

    # Generic message for all failure modes — don't reveal which field was wrong.
    if not username or not password:
        raise AuthenticationError("invalid username or password")

    user = User.query.filter(User.username == str(username).strip().lower()).first()
    if user is None or not user.check_password(password):
        logger.warning("Failed login attempt for username=%r", username)
        raise AuthenticationError("invalid username or password")

    logger.info("User id=%s logged in", user.id)
    return user, _issue_token(user)


def reset_password(user: User, data: dict) -> None:
    current_password = data.get("current_password")
    new_password = data.get("new_password")

    # Generic message whether the field is missing or simply wrong — don't
    # tell a token-holder which one it was.
    if not current_password or not user.check_password(current_password):
        logger.warning("Rejected password reset for user id=%s", user.id)
        raise AuthenticationError("invalid current password")

    if new_password is None or new_password == "":
        raise ValidationError("new_password is required", field="new_password")

    # Model-level validation (min length) raises ValidationError.
    user.set_password(new_password)
    db.session.commit()
    logger.info("Password updated for user id=%s", user.id)


def get_user_by_id(user_id) -> User | None:
    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        return None
    return db.session.get(User, uid)
