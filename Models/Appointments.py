from datetime import datetime, time

from flask import session
from sqlalchemy.orm import validates
from extentions import db
from Models.Users import User
import enum


class AppointmentStatusTypeEnum(enum.Enum):
    SCHEDULED = "Scheduled"
    COMPLETED = "Completed"
    CANCELED = "Canceled"
    
class Appointment(db.Model):
    __tablename__ = "appointment"

    tenant_session = None

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    appointment_start_time = db.Column(db.Time, nullable=True)
    appointment_end_time = db.Column(db.Time, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Scheduled')  # e.g., Scheduled, Completed, Canceled
    duration = db.Column(db.Integer, nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    
    reason = db.Column(db.Text, nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    patient = db.relationship('User', foreign_keys=[patient_id], backref='appointments_as_patient', lazy=True)
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='appointments_as_doctor', lazy=True)
    department = db.relationship('Department', backref='appointments', lazy=True)

    @validates("patient_id", "doctor_id")
    def validate_user_id(self, key, value):
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{key} must be a positive integer")

        session = self.tenant_session or db.session
        user = session.query(User).get(value)
        if not user:
            string = "Patient" if key == "patient_id" else "Doctor"
            raise ValueError(f"{string} not found.")
        return value

    @validates("appointment_date")
    def validate_appointment_date(self, key, value):
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, '%Y-%m-%d')
            except Exception:
                raise ValueError("Appointment data must be a valid date string YYYY-MM-DD")
        elif not isinstance(value, datetime):
            raise ValueError("appointment date must be a datetime object or a date string")
        return value

    @validates("appointment_start_time", "appointment_end_time")
    def appointment_time(self, key, value):
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, "%H:%M").time()
            except ValueError:
                raise ValueError(f"{key} must be a time string in 'HH:MM' format")
        elif not isinstance(value, time):
            raise ValueError(f"{key} must be a time object or time string in 'HH:MM' format")

        session = self.tenant_session or db.session
        appointment_records = session.query(Appointment).filter_by(appointment_date=self.appointment_date, doctor_id=self.doctor_id).all()
        for record in appointment_records:
            if record and (not self.id or record.id != self.id):
                if record.appointment_start_time and record.appointment_end_time:
                    if record.appointment_start_time <= value <= record.appointment_end_time:
                        raise ValueError(f"{key} conflicts with another appointment")

        return value
    
    @validates("reason")
    def validate_reason(self, key, value):
        if not value:
            return ""
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string")
        return value.strip()

    REQUIRED_FIELDS = ["patient_id", "doctor_id", "appointment_date"]

    def __init__(self, **kwargs):
        missing = [field for field in self.REQUIRED_FIELDS if not kwargs.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        super().__init__(**kwargs)