from datetime import datetime

from flask import session
from sqlalchemy.orm import validates, relationship
import json
from extentions import db
from Models.Users import User
from Models.Orders import Orders


# from Models.BillingMedicines import BillingMedicines # Uncomment in your actual project
# from Models.BillingTests import BillingTests         # Uncomment in your actual project
# from Models.BillingSurgeries import BillingSurgeries # Uncomment in your actual project
# from Models.BillingBeds import BillingBeds    # Uncomment in your actual project
# from Models.Prescriptions import Prescriptions       # Uncomment in your actual project
# from Models.Payments import Payment

class Billing(db.Model):
    __tablename__ = "billing"

    tenant_session = None

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)

    total_amount = db.Column(db.Float, default=0)
    amount_paid = db.Column(db.Float, default=0)

    status = db.Column(db.String(50), server_default="PENDING", nullable=True)  # PENDING, PARTIAL_PAYMENT, PAID
    notes = db.Column(db.Text, nullable=True)

    payments = db.relationship("Payment", back_populates="billing")

    order = db.relationship("Orders", back_populates="billing")

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @validates("order_id")
    def validate_order_id(self, key, value):
        if not value or not isinstance(value, int):
            return None

        session = self.tenant_session or db.session
        existing = session.query(Billing).filter(Billing.order_id == value, Billing.id != self.id).first()
        if existing:
            raise ValueError(f"Prescription ID {value} is already billed.")
        return value

    REQUIRED_FIELDS = ["order_id"]

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
