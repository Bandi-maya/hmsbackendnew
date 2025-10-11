import enum
from datetime import datetime
from sqlalchemy.orm import validates
from extentions import db

class Department(db.Model):
    __tablename__ = "department"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @validates("name")
    def validate_name(self, key, value, session=None):
        if not value or not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must be a non-empty string")
        value = value.strip()

        if session:
            existing = session.query(Department).filter(Department.name == value, Department.id != self.id).first()
            if existing:
                raise ValueError("name must be unique")
        return value

    @validates("description")
    def validate_description(self, key, value):
        if not value:
            return ""
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string")
        return value.strip()

    REQUIRED_FIELDS = ["name"]

    def __init__(self, **kwargs):
        missing = [field for field in self.REQUIRED_FIELDS if not kwargs.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        super().__init__(**kwargs)
