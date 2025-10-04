import enum
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import validates

from Models.UserType import UserType
from app_utils import db
from Models.UserExtraFields import UserExtraFields
from Models.Department import Department


class GenderEnum(enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    phone_no = db.Column(db.BigInteger, nullable=False)
    date_of_birth = db.Column(db.DateTime, nullable=False)
    age = db.Column(db.SmallInteger, nullable=False)
    gender = db.Column(db.Enum(GenderEnum), nullable=False)
    address = db.Column(JSON, nullable=False)
    blood_type = db.Column(db.String, nullable=True)

    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=True)

    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)

    user_type_id = db.Column(db.Integer, db.ForeignKey('user_type.id'), nullable=False)
    user_type = db.relationship('UserType', backref=db.backref('users', lazy=True))

    extra_fields = db.relationship("UserExtraFields", backref="user_parent", uselist=False)
    department = db.relationship("Department", backref="user_parent", uselist=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @validates('gender')
    def validate_gender(self, key, value):
        if isinstance(value, str):
            value = value.upper()
            if value not in GenderEnum._member_names_:
                raise ValueError(f"Invalid gender '{value}', must be one of {list(GenderEnum._member_names_)}")
            return GenderEnum[value]
        elif isinstance(value, GenderEnum):
            return value
        else:
            raise ValueError("Gender must be a string or GenderEnum")

    @validates('date_of_birth')
    def validate_date_of_birth(self, key, value):
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, '%Y-%m-%d')
            except Exception:
                raise ValueError("date_of_birth must be a valid date string YYYY-MM-DD")
        elif not isinstance(value, datetime):
            raise ValueError("date_of_birth must be a datetime object or a date string")
        return value

    @validates('phone_no')
    def validate_phone_no(self, key, value):
        try:
            return int(value)
        except Exception:
            raise ValueError("phone_no must be an integer")

    @validates('age')
    def validate_age(self, key, value):
        try:
            age = int(value)
        except Exception:
            raise ValueError("age must be an integer")
        if age < 0 or age > 130:
            raise ValueError("age must be between 0 and 130")
        return age

    @validates('user_type_id')
    def validate_user_type_id(self, key, value):
        try:
            value = int(value)
        except Exception:
            raise ValueError("user_type_id must be an integer")

        # Check if user_type_id exists
        if not UserType.query.get(value):
            raise ValueError(f"user_type_id {value} does not exist in UserType table")

        return value

    @validates('address')
    def validate_address(self, key, value):
        if not isinstance(value, dict):
            raise ValueError("address must be a JSON object")
        return value

    @validates('username')
    def validate_username(self, key, value):
        if not value or not isinstance(value, str) or not value.strip():
            raise ValueError("username must be a non-empty string")
        value = value.strip()

        existing_user = User.query.filter_by(username=value, is_active=True).first()
        if existing_user and (not self.id or existing_user.id != self.id):
            raise ValueError("username must be unique")

        return value

    @validates('email')
    def validate_email(self, key, value):
        if not value or not isinstance(value, str) or not value.strip():
            raise ValueError("email must be a non-empty string")
        value = value.strip()

        existing_user = User.query.filter_by(email=value, is_active=True).first()
        if existing_user and (not self.id or existing_user.id != self.id):
            raise ValueError("email must be unique")

        return value

    @validates('name', 'password')
    def validate_non_empty_strings(self, key, value):
        if not value or not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must be a non-empty string")
        return value.strip()

    REQUIRED_FIELDS = ['name', 'phone_no', 'date_of_birth', 'age', 'gender',
                       'address', 'username', 'email', 'password', 'user_type_id']

    def __init__(self, **kwargs):
        missing = [field for field in self.REQUIRED_FIELDS if not kwargs.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        super().__init__(**kwargs)
