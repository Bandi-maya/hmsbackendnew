from Models.staffSchedule import StaffSchedule
from extentions import ma

class SchedulesSerializer(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = StaffSchedule
        load_instance = True
        include_fk = True

schedule_serializer = SchedulesSerializer()
schedule_serializers = SchedulesSerializer(many=True)


class StaffScheduleSerializer(ma.SQLAlchemyAutoSchema):
    schdules = ma.Nested(schedule_serializers, many=True)

    class Meta:
        model = StaffSchedule
        load_instance = True
        include_fk = True

staff_schedule_serializer = StaffScheduleSerializer()
staff_schedule_serializers = StaffScheduleSerializer(many=True)
