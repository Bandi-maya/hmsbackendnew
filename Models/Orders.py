from datetime import datetime
from sqlalchemy.orm import validates
from extentions import db
from Models.Medicine import Medicine
from Models.Users import User
from Models.PurchaseTest import PurchaseTest
from Models.PurchaseOrder import PurchaseOrder
from Models.PurchaseSurgery import PurchaseSurgery
from Models.Prescriptions import Prescriptions


class Orders(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=True)
    received_date = db.Column(db.Date, nullable=True)
    taken_by = db.Column(db.String(50), nullable=True)
    taken_by_phone_no = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    #Relationships
    user = db.relationship('User', backref='orders', lazy=True)
    billing = db.relationship("Billing", back_populates="order")
    medicines = db.relationship('PurchaseOrder', back_populates='order', cascade="all, delete-orphan")
    lab_tests = db.relationship('PurchaseTest', back_populates='order', cascade="all, delete-orphan")
    surgeries = db.relationship('PurchaseSurgery', back_populates='order', cascade="all, delete-orphan")
    prescription = db.relationship('Prescriptions', backref='order', lazy=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
