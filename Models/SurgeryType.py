from datetime import datetime
from Models.Department import Department

from app_utils import db

class SurgeryType(db.Model):
    __tablename__ = 'surgery_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    department = db.relationship('Department', backref='surgery_types', lazy=True)

    created_At = db.Column(db.DateTime, default=datetime.utcnow)
    updated_At = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    REQUIRED_FIELDS = ['name', 'department_id']

    def __init__(self, **kwargs):
        missing = [f for f in self.REQUIRED_FIELDS if f not in kwargs or kwargs[f] is None]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        super().__init__(**kwargs)
