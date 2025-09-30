from datetime import datetime
from sqlalchemy.orm import validates
from app_utils import db
from Models.Users import User
import enum


class AppointmentStatusTypeEnum(enum.Enum):
    SCHEDULED = "Scheduled"
    COMPLETED = "Completed"
    CANCELED = "Canceled"
    
class Appointment(db.Model):
    __tablename__ = "appointment"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    appointment_start_time = db.Column(db.Time, nullable=True)
    appointment_end_time = db.Column(db.Time, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Scheduled')  # e.g., Scheduled, Completed, Canceled
    duration = db.Column(db.Integer, nullable=True)
    
    
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
        
        user = User.query.get(value)
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

    @validates("appointment_starttime", "appointment_endtime")
    def appointment_time(self, key, value):
        if value is not None and not isinstance(value, datetime.time):
            raise ValueError(f"{key} must be a time object")
        appointment_records = Appointment.query.filter_by(appointment_date=self.appointment_date, doctor_id=self.doctor_id).all()
        for record in appointment_records:
            if key == "appointment_starttime" and record.appointment_starttime and record.appointment_endtime:
                if record.appointment_starttime <= value <= record.appointment_endtime:
                    raise ValueError(f"{key} conflicts with another appointment")
            if key == "appointment_endtime" and record.appointment_starttime and record.appointment_endtime:
                if record.appointment_starttime <= value <= record.appointment_endtime:
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