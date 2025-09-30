from datetime import datetime
from sqlalchemy.orm import validates
from app_utils import db
from Models.Users import User
# from Models.PrescriptionMedicines import PrescriptionMedicines
# from Models.PrescriptionTests import PrescriptionTests

class Prescriptions(db.Model):
    __tablename__ = "prescriptions"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notes = db.Column(db.Text, nullable=True)

    medicines = db.relationship('PrescriptionMedicines', backref='prescriptions', lazy=True)
    tests = db.relationship('PrescriptionTests', backref='prescriptions', lazy=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @validates("patient_id", "doctor_id")
    def validate_name(self, key, value):
        if not value or not isinstance(value, int):
            raise ValueError(f"{key} must be a number")

        existing = User.query.get(value)
        if not existing:
            raise ValueError(f"{key} not found")
        return value

    REQUIRED_FIELDS = ["patient_id", "doctor_id"]
    def __init__(self, **kwargs):
        missing = [field for field in self.REQUIRED_FIELDS if not kwargs.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        super().__init__(**kwargs)
