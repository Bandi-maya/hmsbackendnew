from datetime import datetime
from sqlalchemy.orm import validates
from app_utils import db
from Models.Prescriptions import Prescriptions
from Models.LabTest import LabTest

class BillingTests(db.Model):
    __tablename__ = "billing_tests"

    id = db.Column(db.Integer, primary_key=True)
    billing_id = db.Column(db.Integer, db.ForeignKey('billing.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('lab_test.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @validates("billing_id")
    def validate_name(self, key, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{key} must be a number")

        existing = Prescriptions.query.get(value)
        if not existing:
            raise ValueError(f"Billing not found")
        return value

    @validates("test_id")
    def validate_name(self, key, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{key} must be a number")

        existing = LabTest.query.get(value)
        if not existing:
            raise ValueError(f"Test not found")
        self.price = existing.price
        return value

    REQUIRED_FIELDS = ["billing_id", "test_id"]
    def __init__(self, **kwargs):
        missing = [field for field in self.REQUIRED_FIELDS if not kwargs.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        super().__init__(**kwargs)
