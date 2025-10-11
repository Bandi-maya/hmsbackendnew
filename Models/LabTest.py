from datetime import datetime

from sqlalchemy.orm import validates

from extentions import db


class LabTest(db.Model):
    __tablename__ = 'lab_test'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    is_available = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    REQUIRED_FIELDS = ['name', 'price']

    @validates('name')
    def validate_name(self, key, name):
        if type(name) is not str:
            raise ValueError('name must be a string')
        if not name or not name.strip():
            raise ValueError('Name cannot be empty')
        return name

    @validates('price')
    def validate_price(self, key, price):
        if type(price) is float or type(price) is int:
            return price
        raise ValueError('Price must be a float')

    def __init__(self, **kwargs):
        missing = [field for field in self.REQUIRED_FIELDS if not kwargs.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        super().__init__(**kwargs)
