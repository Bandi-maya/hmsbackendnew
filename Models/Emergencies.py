from datetime import datetime
from extentions import db

class Emergency(db.Model):
    __tablename__ = 'emergencies'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.Text)
    severity = db.Column(db.String(20))
    status = db.Column(db.String(20), default='active')
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    admitted_to_ward = db.Column(db.Integer, db.ForeignKey('ward_beds.id'), nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

