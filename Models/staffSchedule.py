import enum
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.sql import func
# from Models.Users import User

from extentions import db

class ScheduleStatusEnum(enum.Enum):
    scheduled = 'scheduled'
    tentative = 'tentative'
    cancelled = 'cancelled'
    completed = 'completed'

class StaffSchedule(db.Model):
    __tablename__ = 'staff_schedule'

    id = db.Column(db.BigInteger, primary_key=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    staff_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)

    status = db.Column(
        ENUM(ScheduleStatusEnum, name='schedule_status', create_type=False),
        nullable=False,
        default=ScheduleStatusEnum.scheduled
    )

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    staff = db.relationship('User', back_populates='schedule')

    items = db.relationship(
        'Schedule',
        back_populates='staff_schedule',
        cascade='all, delete-orphan'
    )


class Schedule(db.Model):
    __tablename__ = 'schedules'

    id = db.Column(db.BigInteger, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    location = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    staff_schedule_id = db.Column(db.BigInteger, db.ForeignKey('staff_schedule.id'), nullable=False)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    staff_schedule = db.relationship('StaffSchedule', back_populates='items')
