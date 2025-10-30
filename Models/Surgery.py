from datetime import datetime
from extentions import db
from Models.SurgeryType import SurgeryType
from Models.OperationTheatre import OperationTheatre
# from Models.PrescritionSurgeries import PrescriptionSurgeries

class Surgery(db.Model):
    __tablename__ = 'surgeries'

    id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    patient = db.relationship('User', backref='surgeries', lazy=True)

    surgery_type_id = db.Column(db.Integer, db.ForeignKey('surgery_types.id'), nullable=False)
    surgery_type = db.relationship('SurgeryType', backref='surgeries', lazy=True)

    price = db.Column(db.Float, nullable=False, default=0)

    operation_theatre_id = db.Column(db.Integer, db.ForeignKey('operation_theatres.id'), nullable=True)
    operation_theatre = db.relationship('OperationTheatre', backref='surgeries', lazy=True)

    scheduled_start_time = db.Column(db.DateTime, nullable=True)
    scheduled_end_time = db.Column(db.DateTime, nullable=True)

    actual_start_time = db.Column(db.DateTime, nullable=True)
    actual_end_time = db.Column(db.DateTime, nullable=True)

    status = db.Column(db.String(30), default='SCHEDULED')  # Scheduled, In Progress, Completed, Cancelled

    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # prescription_surgeries = db.relationship('PrescriptionSurgeries', lazy=True)

    VALID_STATUSES = {'SCHEDULED', 'In Progress', 'Completed', 'Cancelled'}
    REQUIRED_FIELDS = ['patient_id', 'surgery_type_id']

    def __init__(self, **kwargs):
        missing = [f for f in self.REQUIRED_FIELDS if f not in kwargs or kwargs[f] is None]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        status = kwargs.get('status', 'SCHEDULED')
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Valid options: {', '.join(self.VALID_STATUSES)}")

        super().__init__(**kwargs)

    # def __repr__(self):
    #     return (f"<Surgery(id={self.id}, patient_id={self.patient_id}, surgery_type_id={self.surgery_type_id}, "
    #             f"status='{self.status}', scheduled_start_time={self.scheduled_start_time})>")
