from datetime import datetime
from sqlalchemy.orm import validates
from app_utils import db
from Models.Users import User
# from Models.PrescriptionMedicines import PrescriptionMedicines
# from Models.PrescriptionTests import PrescriptionTests

class Billing(db.Model):
    __tablename__ = "billing"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, default=0)
    status = db.Column(db.String(50), server_default="PENDING", nullable=True)
    notes = db.Column(db.Text, nullable=True)

    medicines = db.relationship('BillingMedicines', backref='prescriptions', lazy=True)
    tests = db.relationship('BillingTests', backref='prescriptions', lazy=True)
    patient = db.relationship('User', foreign_keys=[patient_id], backref='patient_bills', lazy=True)
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='doctor_bills', lazy=True)
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @validates("prescription_id")
    def validate_priscription_id(self, key, value):
        if not value or not isinstance(value, int):
            return None
        existing = Billing.query.filter_by(prescription_id=value).first()
        if existing:
            raise ValueError(f"Already billed")
        return value

    @validates("patient_id")
    def validate_name(self, key, value):
        if not value or not isinstance(value, int):
            raise ValueError(f"{key} must be a number")

        existing = User.query.get(value)
        if not existing:
            raise ValueError(f"{key} not found")
        return value

    REQUIRED_FIELDS = ["patient_id"]
    def __init__(self, **kwargs):
        missing = [field for field in self.REQUIRED_FIELDS if not kwargs.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        super().__init__(**kwargs)
