from datetime import datetime
from extentions import db
from Models.Users import User


class MedicalRecords(db.Model):
    __tablename__ = 'medical_records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notes = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='medical_records', lazy=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
