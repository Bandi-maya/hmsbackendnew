from datetime import datetime
from sqlalchemy.orm import validates
from app_utils import db
from Models.Prescriptions import Prescriptions
from Models.Medicine import Medicine
from Models.MedicineStock import MedicineStock

class BillingMedicines(db.Model):
    __tablename__ = "billing_medicines"

    id = db.Column(db.Integer, primary_key=True)
    billing_id = db.Column(db.Integer, db.ForeignKey('billing.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
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

    @validates("medicine_id")
    def validate_name(self, key, value):
        if not value or not isinstance(value, int):
            raise ValueError(f"{key} must be a number")

        existing = Medicine.query.get(value)
        if not existing:
            raise ValueError(f"Medicine not found")
        return value

    @validates("quantity")
    def validate_name(self, key, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{key} must be a number")
        
        medicine_stock = MedicineStock.query.filter_by(medicine_id=self.medicine_id).first()
        if not medicine_stock:
            return ValueError(f"Something went wrong")
        self.price = medicine_stock.price * value
        return value

    REQUIRED_FIELDS = ["billing_id", "medicine_id"]
    def __init__(self, **kwargs):
        missing = [field for field in self.REQUIRED_FIELDS if not kwargs.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        super().__init__(**kwargs)
