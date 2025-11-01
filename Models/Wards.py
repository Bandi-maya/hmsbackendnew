import enum
from datetime import datetime
from sqlalchemy.orm import validates
from extentions import db
from Models.Department import Department
# from Models.Users import User

class Ward(db.Model):
    __tablename__ = 'ward'

    tenant_session = None

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    ward_type = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    phone_no = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    specialization = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)

    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    department = db.relationship('Department', backref='wards', lazy=True)

    beds = db.relationship('WardBeds', backref='wards')

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    REQUIRED_FIELDS = ["name", "ward_type", "capacity", "department_id"]

    @validates("name")
    def validate_name(self, key, value):
        if not value or not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must be a non-empty string")
        value = value.strip()
        session = self.tenant_session or db.session
        existing = session.query(Ward).filter(Ward.name==value, Ward.id!=getattr(self, 'id', None)).first()
        if existing:
            raise ValueError(f"{key} must be unique")
        return value

    @validates("ward_type")
    def validate_ward_type(self, key, value):
        if not value or not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must be a non-empty string")
        return value.strip()

    @validates("capacity")
    def validate_capacity(self, key, value):
        if not isinstance(value, int):
            raise ValueError(f"{key} must be an integer")
        return value

    @validates("department_id")
    def validate_department_id(self, key, value):
        if not isinstance(value, int):
            raise ValueError(f"{key} must be a number")
        session = self.tenant_session or db.session
        if not session.query(Department).get(value):
            raise ValueError("Department not found")
        return value

    def __init__(self, **kwargs):
        missing = [f for f in self.REQUIRED_FIELDS if f not in kwargs or kwargs[f] is None]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        super().__init__(**kwargs)
