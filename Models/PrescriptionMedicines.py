from datetime import datetime
from sqlalchemy.orm import validates
from extentions import db
from Models.Prescriptions import Prescriptions
from Models.Medicine import Medicine

class PrescriptionMedicines(db.Model):
    __tablename__ = "prescriptions_medicines"

    tenant_session  =None

    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    notes = db.Column(db.Text, nullable=True)
    taken_by = db.Column(db.String(50), nullable=True)
    taken_by_phone_no = db.Column(db.String(50), nullable=True)

    prescription = db.relationship("Prescriptions", back_populates="medicines")

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @validates("prescription_id")
    def validate_name(self, key, value):
        if not value or not isinstance(value, int):
            raise ValueError(f"{key} must be a number")

        session = self.tenant_session or db.session
        existing = session.query(Prescriptions).get(value)
        if not existing:
            raise ValueError(f"Presciption not found")
        return value

    @validates("medicine_id")
    def validate_name(self, key, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{key} must be a number")

        session = self.tenant_session or db.session
        existing = session.query(Medicine).get(value)
        if not existing:
            raise ValueError(f"Medicine not found")
        return value

    @validates("quantity")
    def validate_name(self, key, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{key} must be a number")
        return value

    REQUIRED_FIELDS = ["prescription_id", "medicine_id"]
    def __init__(self, **kwargs):
        missing = [field for field in self.REQUIRED_FIELDS if not kwargs.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        super().__init__(**kwargs)

Prescriptions.medicines = db.relationship(
    'PrescriptionMedicines',
    back_populates='prescription',
    lazy=True
)
