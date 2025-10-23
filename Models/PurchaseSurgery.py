from datetime import datetime
from extentions import db
from Models.SurgeryType import SurgeryType
from Models.OperationTheatre import OperationTheatre

class PurchaseSurgery(db.Model):
    __tablename__ = 'purchase_surgery'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    surgery_type_id = db.Column(db.Integer, db.ForeignKey('surgery_types.id'), nullable=False)
    operation_theatre_id = db.Column(db.Integer, db.ForeignKey('operation_theatres.id'), nullable=True)
    price = db.Column(db.Float, nullable=False, default=0)
    scheduled_date = db.Column(db.DateTime, nullable=True)
    scheduled_start_time = db.Column(db.DateTime, nullable=True)
    scheduled_end_time = db.Column(db.DateTime, nullable=True)
    actual_start_time = db.Column(db.DateTime, nullable=True)
    actual_end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(30), default='SCHEDULED')
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order = db.relationship('Orders', back_populates='surgeries')
    surgery_type = db.relationship('SurgeryType', backref='purchase_surgeries', lazy=True)
    operation_theatre = db.relationship('OperationTheatre', backref='purchase_surgeries', lazy=True)

    VALID_STATUSES = {'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'}
    REQUIRED_FIELDS = ['order_id', 'surgery_type_id']

    def __init__(self, **kwargs):
        missing = [f for f in self.REQUIRED_FIELDS if f not in kwargs or kwargs[f] is None]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        status = kwargs.get('status', 'SCHEDULED')
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Valid options: {', '.join(self.VALID_STATUSES)}")

        super().__init__(**kwargs)

    def __repr__(self):
        return f"<PurchaseSurgery(id={self.id}, order_id={self.order_id}, surgery_type_id={self.surgery_type_id}, status='{self.status}')>"