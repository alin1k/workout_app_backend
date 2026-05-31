from app.extensions import db


class ExerciseSet(db.Model):
    """A single set within an exercise. Table is named `sets`."""

    __tablename__ = "sets"

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

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "exercise_id": self.exercise_id,
            "set_number": self.set_number,
            "reps": self.reps,
            "weight": self.weight,
        }
