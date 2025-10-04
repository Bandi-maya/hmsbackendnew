from flask_jwt_extended import jwt_required
from flask_restful import Resource

from Models.ActivityLogs import ActivityLog
from Serializers.ActivityLogsSerializers import activity_logs_serializers


class ActivityLogsResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        try:
            return activity_logs_serializers.dump(ActivityLog.query.all(), many=True), 200
        except Exception as e:
            print(e)
            return {"error": "Internal error occurred"}, 500