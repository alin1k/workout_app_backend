from app.extensions import db


class ExerciseType(db.Model):
    __tablename__ = "exercise_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    muscle_group = db.Column(db.String(100), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "muscle_group": self.muscle_group,
        }
