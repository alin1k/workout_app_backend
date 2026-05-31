from sqlalchemy.orm import validates

from app.extensions import db
from app.services.errors import ValidationError


class ExerciseType(db.Model):
    __tablename__ = "exercise_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    muscle_group = db.Column(db.String(100), nullable=True)

    @validates("name")
    def _validate_name(self, key, value):
        if value is None or not str(value).strip():
            raise ValidationError("name is required", field=key)
        return str(value).strip()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "muscle_group": self.muscle_group,
        }
