from sqlalchemy.dialects.postgresql import JSONB
from app_utils import db

class UserExtraFields(db.Model):
    __tablename__ = "user_extra_fields"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    fields_data = db.Column(JSONB, nullable=True)

    user = db.relationship("User", back_populates="extra_fields")
