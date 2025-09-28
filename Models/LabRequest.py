from datetime import datetime
from app_utils import db
from Models.Users import User
from Models.LabTest import LabTest


class LabRequest(db.Model):
    __tablename__ = 'lab_request'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('lab_test.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="pending")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = db.relationship('User', foreign_keys=[patient_id])
    test = db.relationship('LabTest', foreign_keys=[test_id])

    REQUIRED_FIELDS = ['patient_id', 'test_id']

    def __init__(self, **kwargs):
        missing = [field for field in self.REQUIRED_FIELDS if not kwargs.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        super().__init__(**kwargs)
