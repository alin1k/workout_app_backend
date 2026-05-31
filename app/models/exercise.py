from sqlalchemy import CheckConstraint
from sqlalchemy.orm import validates

from app.extensions import db
from app.services.errors import ValidationError


class Exercise(db.Model):
    __tablename__ = "exercises"
    __table_args__ = (
        # `order` is a SQL reserved word, so it must be quoted in the CHECK expression.
        CheckConstraint('"order" > 0', name="ck_exercises_order_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(
        db.Integer,
        db.ForeignKey("workouts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exercise_type_id = db.Column(
        db.Integer,
        db.ForeignKey("exercise_types.id"),
        nullable=False,
        index=True,
    )
    order = db.Column(db.Integer, nullable=False, default=1)

    workout = db.relationship("Workout", back_populates="exercises")
    exercise_type = db.relationship("ExerciseType")
    sets = db.relationship(
        "ExerciseSet",
        back_populates="exercise",
        cascade="all, delete-orphan",
        order_by="ExerciseSet.set_number",
    )

    @validates("order")
    def _validate_order(self, key, value):
        if value is None:
            raise ValidationError("order is required", field=key)
        try:
            ivalue = int(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError("order must be an integer", field=key) from exc
        if ivalue <= 0:
            raise ValidationError("order must be positive", field=key)
        return ivalue

    def to_dict(self, include_sets: bool = True) -> dict:
        out = {
            "id": self.id,
            "workout_id": self.workout_id,
            "exercise_type_id": self.exercise_type_id,
            "exercise_type": self.exercise_type.to_dict() if self.exercise_type else None,
            "order": self.order,
        }
        if include_sets:
            out["sets"] = [s.to_dict() for s in self.sets]
        return out
