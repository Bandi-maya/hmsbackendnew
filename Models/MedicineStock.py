from datetime import datetime
from app_utils import db
from Models.Medicine import Medicine


class MedicineStock(db.Model):
    __tablename__ = 'medicine_stock'

    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    batch_no = db.Column(db.String(50), nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    price = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    medicine = db.relationship('Medicine', backref='stocks', lazy=True)

    REQUIRED_FIELDS = ['medicine_id', 'quantity', 'batch_no', 'expiry_date', 'price']

    def __init__(self, **kwargs):
        missing = [f for f in self.REQUIRED_FIELDS if f not in kwargs or kwargs[f] is None]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        super().__init__(**kwargs)
