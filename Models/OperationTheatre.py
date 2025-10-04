from datetime import datetime

from app_utils import db


class OperationTheatre(db.Model):
    __tablename__ = 'operation_theatres'

    VALID_STATUSES = {'AVAILABLE', 'In Use', 'Under Maintenance', 'Cleaning', 'Out of Service'}
    REQUIRED_FIELDS = ['name', 'department_id']

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

    # Location info
    building = db.Column(db.String(100), nullable=True)
    floor = db.Column(db.String(20), nullable=True)
    wing = db.Column(db.String(50), nullable=True)
    room_number = db.Column(db.String(20), nullable=True)

    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    status = db.Column(db.String(20), default='AVAILABLE')
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, **kwargs):
        # Check for required fields presence and not None
        missing = [f for f in self.REQUIRED_FIELDS if f not in kwargs or kwargs[f] is None]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        # Validate status if provided
        status = kwargs.get('status', 'AVAILABLE')
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Valid options: {', '.join(self.VALID_STATUSES)}")

        # Validate string lengths (optional, to avoid db errors)
        if 'name' in kwargs and len(kwargs['name']) > 50:
            raise ValueError("Field 'name' exceeds max length of 50 characters")

        if 'building' in kwargs and kwargs['building'] and len(kwargs['building']) > 100:
            raise ValueError("Field 'building' exceeds max length of 100 characters")

        if 'floor' in kwargs and kwargs['floor'] and len(kwargs['floor']) > 20:
            raise ValueError("Field 'floor' exceeds max length of 20 characters")

        if 'wing' in kwargs and kwargs['wing'] and len(kwargs['wing']) > 50:
            raise ValueError("Field 'wing' exceeds max length of 50 characters")

        if 'room_number' in kwargs and kwargs['room_number'] and len(kwargs['room_number']) > 20:
            raise ValueError("Field 'room_number' exceeds max length of 20 characters")

        # Call parent constructor to set attributes
        super().__init__(**kwargs)

    def validate(self):
        """
        Can be called explicitly to validate the current instance
        Useful before updating or saving
        """
        if not self.name or len(self.name) > 50:
            raise ValueError("Field 'name' is required and must be at most 50 characters")

        if not self.department_id:
            raise ValueError("Field 'department_id' is required")

        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status '{self.status}'. Valid options: {', '.join(self.VALID_STATUSES)}")

        # Additional length validations on optional fields
        for field_name, max_len in [('building', 100), ('floor', 20), ('wing', 50), ('room_number', 20)]:
            value = getattr(self, field_name)
            if value and len(value) > max_len:
                raise ValueError(f"Field '{field_name}' exceeds max length of {max_len} characters")

    def __repr__(self):
        return f"<OperationTheatre(id={self.id}, name='{self.name}', status='{self.status}')>"
