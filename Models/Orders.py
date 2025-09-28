from datetime import datetime
from sqlalchemy.orm import validates
from app_utils import db
from Models.Medicine import Medicine
from Models.Users import User  # <<< Add this import!


class Orders(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    received_date = db.Column(db.Date, nullable=True)
    taken_by = db.Column(db.String(50), nullable=True)
    taken_by_phone_no = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='orders', lazy=True)
    items = db.relationship('PurchaseOrder', back_populates='order', cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
