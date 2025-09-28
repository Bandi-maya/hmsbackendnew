from datetime import datetime

from sqlalchemy.orm import validates

from app_utils import db


class UserType(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    type = db.Column(db.String, nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    REQUIRED_FIELDS = ['type']

    @validates('type', 'description')
    def validate_type(self, key, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must be a non-empty string")

        if key == 'type':
            existing_user_type = UserType.query.filter_by(type=value, is_active=True).first()
            if existing_user_type and (not self.id or existing_user_type.id != self.id):
                raise ValueError("Type must be unique")

        return value.strip()

    def __init__(self, **kwargs):
        missingFields = [field for field in self.REQUIRED_FIELDS if not kwargs.get(field)]
        if missingFields:
            raise ValueError(f"Missing required fields: {', '.join(missingFields)}")

        super().__init__(**kwargs)