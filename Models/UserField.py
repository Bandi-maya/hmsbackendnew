import enum
from sqlalchemy.orm import validates
from Models.UserType import UserType
from app_utils import db


class FieldTypeEnum(enum.Enum):
    STRING = "STRING"
    INTEGER = "INTEGER"
    JSON = "JSON"

class UserFieldStatusTypeEnum(enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    


class UserField(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_type = db.Column(db.Integer, db.ForeignKey('user_type.id'), nullable=False)
    field_name = db.Column(db.String(100), nullable=False)
    is_mandatory = db.Column(db.Boolean, default=False)
    status = db.Column(db.Enum(UserFieldStatusTypeEnum), nullable=False, default=UserFieldStatusTypeEnum.INACTIVE)
    field_type = db.Column(db.Enum(FieldTypeEnum), default=FieldTypeEnum.STRING)

    @validates("user_type")
    def validate_user_type_id(self, key, value):
        try:
            value = int(value)
        except Exception:
            raise ValueError("user_type must be an integer")

        if not UserType.query.get(value):
            raise ValueError(f"user_type {value} does not exist in UserType table")

        return value

    @validates("field_name")
    def validate_field_name(self, key, value):
        if not value or not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must be a non-empty string")
        value = value.strip()

        existing_user_field = UserField.query.filter_by(field_name=value, user_type=self.user_type).first()
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
