import enum
from datetime import datetime
from sqlalchemy.orm import validates
from extentions import db
from Models.Wards import Ward
from Models.Users import User

class WardBedStatusEnum(enum.Enum):
    AVAILABLE = 'AVAILABLE'
    UNAVAILABLE = 'UNAVAILABLE'
    OCCUPIED = 'OCCUPIED'
    UNDER_MAINTENANCE = 'UNDER_MAINTENANCE'

class WardBeds(db.Model):
    __tablename__ = 'ward_beds'

    tenant_session = None

    id = db.Column(db.Integer, primary_key=True)
    bed_no = db.Column(db.String, nullable=False)
    ward_id = db.Column(db.Integer, db.ForeignKey('ward.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='AVAILABLE')
    admission_date = db.Column(db.DateTime, nullable=True)
    price = db.Column(db.Float, nullable=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)

    billing = db.relationship("Billing", back_populates="bed")

    patient = db.relationship('User', foreign_keys=[patient_id], lazy=True)
    ward = db.relationship('Ward', backref='ward_beds', lazy=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    REQUIRED_FIELDS = ["bed_no", "ward_id"]

    @validates("bed_no")
    def validate_name(self, key, value):
        if not value or not isinstance(value, str):
            raise ValueError(f"{key} must be a non-empty string")

        return value

    @validates("ward_id")
    def validate_ward_type(self, key, value):
        if not value or not isinstance(value, int):
            raise ValueError(f"{key} must be a non-empty string")
        session = self.tenant_session or db.session
        existing = session.query(Ward).get(int(value))
        if not existing:
            raise ValueError(f"Ward {value} does not exist")
        return value

    def __init__(self, **kwargs):
        missing = [f for f in self.REQUIRED_FIELDS if f not in kwargs or kwargs[f] is None]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        super().__init__(**kwargs)
