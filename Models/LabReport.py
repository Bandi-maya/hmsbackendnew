from datetime import datetime
from extentions import db


class LabReport(db.Model):
    __tablename__ = 'lab_report'

    id = db.Column(db.Integer, primary_key=True)
    # request_id = db.Column(db.Integer, db.ForeignKey('lab_request.id'), nullable=False)
    report_data = db.Column(db.JSON, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # lab_request = db.relationship('LabRequest', foreign_keys=[request_id])

    REQUIRED_FIELDS = ['request_id', 'report_data']

    def __init__(self, **kwargs):
        missing = [field for field in self.REQUIRED_FIELDS if not kwargs.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        super().__init__(**kwargs)
