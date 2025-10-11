from datetime import datetime
from extentions import db

class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # Who did the action
    action = db.Column(db.String(255), nullable=False)  # e.g., "CREATE_PATIENT", "DELETE_MEDICINE"
    details = db.Column(db.Text, nullable=True)  # JSON or string of what was changed
    ip_address = db.Column(db.String(45), nullable=True)  # Optional
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
