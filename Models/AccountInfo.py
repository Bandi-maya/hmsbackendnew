from datetime import datetime
from sqlalchemy.orm import validates
from app_utils import db

class AccountInfo(db.Model):
    __tablename__ = "account_info"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    logo_url = db.Column(db.String, nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @validates("logo_url")
    def validate_logo_url(self, key, value):
        if not value:
            return ""
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string")
        return value.strip()

    @validates("name")
    def validate_name(self, key, value):
        if not value:
            return ""
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string")
        return value.strip()

    REQUIRED_FIELDS = ["name", "logo_url"]

    def __init__(self, **kwargs):
        missing = [field for field in self.REQUIRED_FIELDS if not kwargs.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        super().__init__(**kwargs)