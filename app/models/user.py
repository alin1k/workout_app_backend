from datetime import datetime, timezone

from sqlalchemy.orm import validates
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.services.errors import ValidationError


AVATAR_CODE_MAX = 64


def _default_avatar_code(context):
    # A new account's picture is seeded from its (already normalised) username.
    return context.get_current_parameters()["username"]


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    # Seed for the generated profile picture — the client renders the avatar
    # from this string, so no image is ever stored.
    avatar_code = db.Column(
        db.String(AVATAR_CODE_MAX), nullable=False, default=_default_avatar_code
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    workouts = db.relationship(
        "Workout",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    @validates("username")
    def _validate_username(self, key, value):
        if value is None or not str(value).strip():
            raise ValidationError("username is required", field=key)
        v = str(value).strip().lower()
        if len(v) < 3:
            raise ValidationError("username must be at least 3 characters", field=key)
        if len(v) > 64:
            raise ValidationError("username must be at most 64 characters", field=key)
        return v

    @validates("avatar_code")
    def _validate_avatar_code(self, key, value):
        if value is None:
            raise ValidationError("avatar_code is required", field=key)
        if not isinstance(value, str):
            raise ValidationError("avatar_code must be a string", field=key)
        v = value.strip()
        if not v:
            raise ValidationError("avatar_code is required", field=key)
        if len(v) > AVATAR_CODE_MAX:
            raise ValidationError(
                f"avatar_code must be at most {AVATAR_CODE_MAX} characters", field=key
            )
        return v

    def set_password(self, plain: str) -> None:
        if not plain or len(plain) < 8:
            raise ValidationError(
                "password must be at least 8 characters", field="password"
            )
        # werkzeug uses scrypt by default — strong, no extra deps.
        self.password_hash = generate_password_hash(plain)

    def check_password(self, plain: str) -> bool:
        if not plain:
            return False
        return check_password_hash(self.password_hash, plain)

    def to_dict(self) -> dict:
        # password_hash is intentionally never serialized.
        # Scalar columns only — admin_service calls this once per row of a
        # LEFT JOIN'd listing, so touching `self.workouts` here would turn
        # that single query into an N+1.
        return {
            "id": self.id,
            "username": self.username,
            "is_admin": self.is_admin,
            "avatar_code": self.avatar_code,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
