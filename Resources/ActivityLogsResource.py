from flask_jwt_extended import jwt_required
from flask_restful import Resource
import logging
from new import with_tenant_session_and_user
from Serializers.ActivityLogsSerializers import activity_logs_serializers
from Models.ActivityLogs import ActivityLog

logger = logging.getLogger(__name__)

class ActivityLogsResource(Resource):
    method_decorators = [jwt_required()]

    # ✅ GET all activity logs
    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            logs = tenant_session.query(ActivityLog).all()
            return activity_logs_serializers.dump(logs), 200
        except Exception:
            logger.exception("Error fetching activity logs")
            return {"error": "Internal error occurred"}, 500
