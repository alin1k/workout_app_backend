from datetime import datetime, timezone

from sqlalchemy.orm import validates

from app.extensions import db
from app.services.errors import ValidationError


class Workout(db.Model):
    __tablename__ = "workouts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(255), nullable=False)
    performed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user = db.relationship("User", back_populates="workouts")
    exercises = db.relationship(
        "Exercise",
        back_populates="workout",
        cascade="all, delete-orphan",
        order_by="Exercise.order",
    )

    @validates("name")
    def _validate_name(self, key, value):
        if value is None or not str(value).strip():
            raise ValidationError("name is required", field=key)
        return str(value).strip()

    def to_dict(self, include_exercises: bool = True) -> dict:
        out = {
            "id": self.id,
            "name": self.name,
            "performed_at": self.performed_at.isoformat() if self.performed_at else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_exercises:
            out["exercises"] = [e.to_dict() for e in self.exercises]
        else:
            out["exercise_count"] = len(self.exercises)
            out["set_count"] = sum(len(e.sets) for e in self.exercises)
            out["muscle_groups"] = sorted({
                e.exercise_type.muscle_group
                for e in self.exercises
                if e.exercise_type is not None and e.exercise_type.muscle_group
            })
        return out
