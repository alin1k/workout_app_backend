from datetime import datetime, timezone

from app.extensions import db


class Workout(db.Model):
    __tablename__ = "workouts"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    performed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    exercises = db.relationship(
        "Exercise",
        back_populates="workout",
        cascade="all, delete-orphan",
        order_by="Exercise.order",
    )

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
        return out
