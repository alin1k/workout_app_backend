from datetime import datetime, timezone

from sqlalchemy.orm import validates
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.services.errors import ValidationError


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
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
        return {
            "id": self.id,
            "username": self.username,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
