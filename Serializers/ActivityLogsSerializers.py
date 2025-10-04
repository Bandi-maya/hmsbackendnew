from Models.ActivityLogs import ActivityLog
from app_utils import ma

class ActivityLogsSerializer(ma.SQLAlchemyAutoSchema):

    class Meta:
        model = ActivityLog
        load_instance = True
        include_fk = True

activity_logs_serializer = ActivityLogsSerializer()
activity_logs_serializers = ActivityLogsSerializer(many=True)