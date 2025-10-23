from datetime import datetime
from sqlalchemy.orm import validates

from extentions import db
from Models.Prescriptions import Prescriptions
from Models.LabTest import LabTest

class PrescriptionTests(db.Model):
    __tablename__ = "prescriptions_tests"

    tenant_session = None

    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=True)
    test_id = db.Column(db.Integer, db.ForeignKey('lab_test.id'), nullable=False)
    status = db.Column(db.String, nullable=True, default="PENDING")
    notes = db.Column(db.Text, nullable=True)

    # ✅ Corrected back_populates name to match Prescriptions.tests
    prescription = db.relationship("Prescriptions", back_populates="tests")

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @validates("prescription_id")
    def validate_prescription_id(self, key, value):
        if not value or not isinstance(value, int):
            raise ValueError(f"{key} must be a number")
        session = self.tenant_session or db.session
        existing = session.query(Prescriptions).get(value)
        if not existing:
            raise ValueError("Prescription not found")
        return value

    @validates("test_id")
    def validate_test_id(self, key, value):
        if not value or not isinstance(value, int):
            raise ValueError(f"{key} must be a number")
        session = self.tenant_session or db.session
        existing = session.query(LabTest).get(value)
        if not existing:
            raise ValueError("Test not found")
        return value

    REQUIRED_FIELDS = ["prescription_id", "test_id"]
    def __init__(self, **kwargs):
        missing = [field for field in self.REQUIRED_FIELDS if not kwargs.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        super().__init__(**kwargs)

Prescriptions.tests = db.relationship(
    'PrescriptionTests',
    back_populates='prescription',
    lazy=True
)
