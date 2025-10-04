from app_utils import db


class Surgeon(db.Model):
    __tablename__ = 'surgeons'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=True)
    # Add other fields as needed
    