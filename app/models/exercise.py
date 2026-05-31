from app.extensions import db


class Exercise(db.Model):
    __tablename__ = "exercises"

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
