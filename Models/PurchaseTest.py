from datetime import datetime
from extentions import db
from Models.LabTest import LabTest


class PurchaseTest(db.Model):
    __tablename__ = 'purchase_test'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('lab_test.id'), nullable=False)
    status = db.Column(db.String, nullable=True, default="PENDING")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order = db.relationship('Orders', back_populates='lab_tests')
    lab_test = db.relationship('LabTest', backref='purchase_test', lazy=True)

    REQUIRED_FIELDS = ['test_id']

    def __init__(self, **kwargs):
        missing = [f for f in self.REQUIRED_FIELDS if f not in kwargs or kwargs[f] is None]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        super().__init__(**kwargs)
