import enum
from datetime import datetime

from sqlalchemy.orm import validates
from Models.UserType import UserType
from extentions import db


class FieldTypeEnum(enum.Enum):
    STRING = "STRING"
    INTEGER = "INTEGER"
    JSON = "JSON"

class UserField(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    tenant_session = None

    user_type = db.Column(db.Integer, db.ForeignKey('user_type.id'), nullable=False)
    field_name = db.Column(db.String(100), nullable=False)
    is_mandatory = db.Column(db.Boolean, default=False)
    field_type = db.Column(db.Enum(FieldTypeEnum), default=FieldTypeEnum.STRING)
    is_active = db.Column(db.Boolean, default=True)
    is_deleted = db.Column(db.Boolean, default=False)

    user_type_data = db.relationship('UserType', backref=db.backref('users_field', lazy=True))

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    @validates("user_type")
    def validate_user_type_id(self, key, value):
        try:
            value = int(value)
        except Exception:
            raise ValueError("user_type must be an integer")
        session = self.tenant_session or db.session
        if not session.query(UserType).get(value):
            raise ValueError(f"user_type {value} does not exist in UserType table")

        return value

    @validates("field_name")
    def validate_field_name(self, key, value):
        if not value or not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must be a non-empty string")
        value = value.strip()

        session = self.tenant_session or db.session
        existing_user_field = session.query(UserField).filter_by(field_name=value, user_type=self.user_type).first()
        if existing_user_field and (not self.id or existing_user_field.id != self.id):
            raise ValueError(f"field_name '{key}' must be unique per user_type")

        return value

    @validates("is_mandatory")
    def validate_is_mandatory(self, key, value):
        if not isinstance(value, bool):
            raise ValueError("is_mandatory must be a boolean")
        return value

    @validates("field_type")
    def validate_field_type(self, key, value):
        if isinstance(value, str):
            value = value.upper()
            if value not in FieldTypeEnum._member_names_:
                raise ValueError(f"Invalid field_type '{value}', must be one of {list(FieldTypeEnum._member_names_)}")
            return FieldTypeEnum[value]
        elif isinstance(value, FieldTypeEnum):
            return value
        else:
            raise ValueError(f"field_type must be a string or FieldTypeEnum ({list(FieldTypeEnum._member_names_)})")

    REQUIRED_FIELDS = ['field_type', 'user_type', 'field_name']

    def __init__(self, **kwargs):
        missing_fields = [field for field in self.REQUIRED_FIELDS if field not in kwargs]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        super().__init__(**kwargs)
