from datetime import datetime
from sqlalchemy.orm import validates

from Models.WardBeds import WardBeds
from app_utils import db
from Models.Prescriptions import Prescriptions


class BillingBeds(db.Model):
    __tablename__ = "billing_beds"

    id = db.Column(db.Integer, primary_key=True)
    billing_id = db.Column(db.Integer, db.ForeignKey('billing.id'), nullable=False)
    bed_id = db.Column(db.Integer, db.ForeignKey('ward_beds.id'), nullable=False)
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

    @validates("bed_id")
    def validate_name(self, key, value):
        if not value or not isinstance(value, int):
            raise ValueError(f"{key} must be a number")

        existing = WardBeds.query.get(value)
        if not existing:
            raise ValueError(f"Bed not found")
        return value

    REQUIRED_FIELDS = ["billing_id", "bed_id"]

    def __init__(self, **kwargs):
        missing = [field for field in self.REQUIRED_FIELDS if not kwargs.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        super().__init__(**kwargs)
