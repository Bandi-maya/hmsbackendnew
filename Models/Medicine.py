from datetime import datetime
from sqlalchemy.orm import validates
from extentions import db
from Models.MedicineStock import MedicineStock


class Medicine(db.Model):
    __tablename__ = 'medicine'

    tenant_session = None

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    manufacturer = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to MedicineStock
    medicine_stock = db.relationship('MedicineStock', backref='medicine', lazy=True)

    REQUIRED_FIELDS = ['name']

    @validates('name')
    def validate_name(self, key, value):
        """Ensure medicine name is unique and non-empty."""
        if not value or not value.strip():
            raise ValueError("Medicine name must be a non-empty string")

        value = value.strip()

        session = self.tenant_session or db.session
        existing = session.query(Medicine).filter(
            Medicine.name == value,
            Medicine.id != getattr(self, 'id', None)
        ).first()

        if existing:
            raise ValueError("Medicine name must be unique")

        return value

    @validates('manufacturer')
    def validate_manufacturer(self, key, value):
        """Clean up manufacturer name."""
        return value.strip() if value else None

    def __init__(self, **kwargs):
        missing = [f for f in self.REQUIRED_FIELDS if f not in kwargs or kwargs[f] is None]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        super().__init__(**kwargs)
