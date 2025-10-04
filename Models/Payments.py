from datetime import datetime

from app_utils import db


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    billing_id = db.Column(db.Integer, db.ForeignKey('billing.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(50), nullable=False)  # e.g., "cash", "card", "upi"
    transaction_ref = db.Column(db.String(100), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __init__(self, billing_id, amount, method, transaction_ref=None):
        if amount <= 0:
            raise ValueError("Payment amount must be positive.")
        self.billing_id = billing_id
        self.amount = amount
        self.method = method
        self.transaction_ref = transaction_ref
