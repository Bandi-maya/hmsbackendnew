from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
import logging

from sqlalchemy import or_, cast, String

from new import with_tenant_session_and_user
from Serializers.ActivityLogsSerializers import activity_logs_serializers
from Models.ActivityLogs import ActivityLog

logger = logging.getLogger(__name__)

class ActivityLogsResource(Resource):
    method_decorators = [jwt_required()]

    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        """
        Retrieves paginated activity logs for a tenant.
        Supports optional search query 'q' across multiple fields.
        """
        try:
            query = tenant_session.query(ActivityLog)

            # 🔹 Search query
            q = request.args.get('q')
            if q:
                query = query.filter(
                    or_(
                        cast(ActivityLog.user_id, String).ilike(f"%{q}%"),
                        ActivityLog.action.ilike(f"%{q}%"),
                        ActivityLog.details.ilike(f"%{q}%"),
                        ActivityLog.ip_address.ilike(f"%{q}%"),
                    )
                )

            # 🔹 Pagination parameters
            page = request.args.get("page", default=1, type=int)
            limit = request.args.get("limit", default=20, type=int)

            if page < 1: page = 1
            if limit < 1: limit = 20

            total_records = query.count()
            logs = query.offset((page - 1) * limit).limit(limit).all()
            result = activity_logs_serializers.dump(logs)

            return {
                "page": page,
                "limit": limit,
                "total_records": total_records,
                "total_pages": (total_records + limit - 1) // limit if limit else 1,
                "data": result
            }, 200

        except Exception:
            logger.exception("Error fetching activity logs")
            return {"error": "Internal error occurred"}, 500
