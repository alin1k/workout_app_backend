from sqlalchemy import CheckConstraint
from sqlalchemy.orm import validates

from app.extensions import db
from app.services.errors import ValidationError


class ExerciseSet(db.Model):
    """A single set within an exercise. Table is named `sets`."""

    __tablename__ = "sets"
    __table_args__ = (
        CheckConstraint("reps > 0", name="ck_sets_reps_positive"),
        CheckConstraint("set_number > 0", name="ck_sets_set_number_positive"),
        CheckConstraint("weight IS NULL OR weight >= 0", name="ck_sets_weight_non_negative"),
    )

    id = db.Column(db.Integer, primary_key=True)
    exercise_id = db.Column(
        db.Integer,
        db.ForeignKey("exercises.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    set_number = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=True)

    exercise = db.relationship("Exercise", back_populates="sets")

    @validates("reps")
    def _validate_reps(self, key, value):
        if value is None:
            raise ValidationError("reps is required", field=key)
        try:
            ivalue = int(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError("reps must be an integer", field=key) from exc
        if ivalue <= 0:
            raise ValidationError("reps must be positive", field=key)
        return ivalue

    @validates("set_number")
    def _validate_set_number(self, key, value):
        if value is None:
            raise ValidationError("set_number is required", field=key)
        try:
            ivalue = int(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError("set_number must be an integer", field=key) from exc
        if ivalue <= 0:
            raise ValidationError("set_number must be positive", field=key)
        return ivalue

    @validates("weight")
    def _validate_weight(self, key, value):
        if value is None:
            return None
        try:
            fvalue = float(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError("weight must be a number", field=key) from exc
        if fvalue < 0:
            raise ValidationError("weight cannot be negative", field=key)
        return fvalue

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "exercise_id": self.exercise_id,
            "set_number": self.set_number,
            "reps": self.reps,
            "weight": self.weight,
        }
