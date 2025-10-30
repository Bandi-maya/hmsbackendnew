# from datetime import datetime

# from extentions import db

# class SurgeryDoctor(db.Model):
#     __tablename__ = 'surgery_doctors'

#     id = db.Column(db.Integer, primary_key=True)
#     surgery_id = db.Column(db.Integer, db.ForeignKey('surgeries.id'), nullable=False)
#     doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

#     role = db.Column(db.String(50), nullable=False)  # e.g., 'Primary Surgeon', 'Assistant Surgeon', 'Anesthetist'

#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

#     # Relationships (optional for easier navigation)
#     surgery = db.relationship("Surgery", backref='surgery_doctors', lazy=True)
#     doctor = db.relationship('User', backref='surgery_doctors', lazy=True)

#     def __repr__(self):
#         return f"<SurgeryDoctor(surgery_id={self.surgery_id}, doctor_id={self.doctor_id}, role='{self.role}')>"
