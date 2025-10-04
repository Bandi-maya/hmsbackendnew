from datetime import datetime
from sqlalchemy.orm import validates, relationship
import json
from app_utils import db
from Models.Users import User


from Models.BillingMedicines import BillingMedicines # Uncomment in your actual project
from Models.BillingTests import BillingTests         # Uncomment in your actual project
from Models.BillingSurgeries import BillingSurgeries # Uncomment in your actual project
from Models.BillingBeds import BillingBeds    # Uncomment in your actual project
# from Models.Prescriptions import Prescriptions       # Uncomment in your actual project
from Models.Payments import Payment

class Billing(db.Model):
    __tablename__ = "billing"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=True, unique=True)

    total_amount = db.Column(db.Float, default=0)
    amount_paid = db.Column(db.Float, default=0)

    status = db.Column(db.String(50), server_default="PENDING", nullable=True)  # PENDING, PARTIAL_PAYMENT, PAID
    notes = db.Column(db.Text, nullable=True)

    # Removed: logs = db.Column(db.Text)

    medicines = db.relationship('BillingMedicines', backref='prescriptions', lazy=True)
    tests = db.relationship('BillingTests', backref='prescriptions', lazy=True)
    beds = db.relationship('BillingBeds', backref='billing', lazy=True)
    surgeries = db.relationship('BillingSurgeries', backref='billing', lazy=True)

    # New relationship
    payments = db.relationship('Payment', backref='billing', lazy=True, cascade="all, delete-orphan")

    patient = db.relationship('User', foreign_keys=[patient_id], backref='patient_bills', lazy=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @validates("prescription_id")
    def validate_priscription_id(self, key, value):
        if not value or not isinstance(value, int):
            return None
        existing = Billing.query.filter(Billing.prescription_id == value, Billing.id != self.id).first()
        if existing:
            raise ValueError(f"Prescription ID {value} is already billed.")
        return value

    @validates("patient_id")
    def validate_user_id(self, key, value):
        if not value or not isinstance(value, int):
            raise ValueError(f"{key} must be a valid integer ID.")
        existing = User.query.get(value)
        if not existing:
            raise ValueError(f"User (ID: {value}) for {key} not found.")
        return value

    REQUIRED_FIELDS = ["patient_id"]

    def __init__(self, **kwargs):
        missing = [field for field in self.REQUIRED_FIELDS if not kwargs.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        super().__init__(**kwargs)

    def update_status_based_on_payments(self):
        self.amount_paid = sum(payment.amount for payment in self.payments or [])
        if self.amount_paid >= self.total_amount:
            self.status = "PAID"
        elif self.amount_paid > 0:
            self.status = "PARTIAL_PAYMENT"
        else:
            self.status = "PENDING"
