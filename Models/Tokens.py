from datetime import datetime
from sqlalchemy.orm import validates
from app_utils import db
from Models.Users import User
import enum
from Models.Department import Department

class Token(db.Model):
    __tablename__ = "Token"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    appointment_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Alloted')  # e.g., Scheduled, Completed, Canceled
    token_number = db.Column(db.Integer, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)

    patient = db.relationship('User', foreign_keys=[patient_id], backref='patient_tokens', lazy=True)
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='doctor_tokens', lazy=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @validates("doctor_id")
    def validate_doctor_id(self, key, value):
        if value is not None:
            if not isinstance(value, int) or value <= 0:
                return None
            user = User.query.get(value)
            if not user:
                raise ValueError("Doctor not found.")
        return value
    
    @validates("patient_id")
    def validate_user_id(self, key, value):
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{key} must be a positive integer")
        user = User.query.get(value)
        if not user:
            string = "Patient" if key == "patient_id" else "Doctor"
            raise ValueError(f"{string} not found.")
        return value
    
    @validates("department_id")
    def validate_department_id(self, key, value):
        if value is not None:
            if not isinstance(value, int) or value <= 0:
                raise ValueError(f"{key} must be a positive integer")
            department = Department.query.get(value)
            if not department:
                raise ValueError("Department not found.")
        return value
    
    @validates("appointment_date")
    def validate_appointment_date(self, key, value):
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, '%Y-%m-%d')
            except Exception:
                raise ValueError("appointment date must be a valid date string YYYY-MM-DD")
        elif not isinstance(value, datetime):
            raise ValueError("appointment date must be a datetime object or a date string")
    
        self.token_number = Token.query.filter_by(department_id = self.department_id,appointment_date=self.appointment_date).count() + 1
        return value
