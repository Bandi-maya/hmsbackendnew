from datetime import datetime
from sqlalchemy.orm import validates
from extentions import db
# from Models.Users import User
# from Models.PrescriptionMedicines import PrescriptionMedicines
# from Models.PrescriptionTests import PrescriptionTests

class Prescriptions(db.Model):
    __tablename__ = "prescriptions"

    tenant_session = None

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)

    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='prescriptions_as_doctor', lazy=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @validates("doctor_id")
    def validate_doctor_id(self, key, value):
        if not value or not isinstance(value, int):
            raise ValueError(f"{key} must be a number")

        session = self.tenant_session or db.session
        print(value)
        existing = session.query(User).get(value)
        print(existing)
        if not existing:
            raise ValueError(f"{key} not found")
        return value

    REQUIRED_FIELDS = ["doctor_id"]
    def __init__(self, **kwargs):
        missing = [field for field in self.REQUIRED_FIELDS if not kwargs.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        super().__init__(**kwargs)
