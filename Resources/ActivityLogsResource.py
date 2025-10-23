from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
import logging

from sqlalchemy import or_

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
            query = tenant_session.query(ActivityLog)

            # 🔹 Pagination parameters
            page = request.args.get("page", type=int)
            limit = request.args.get("limit", type=int)

            q = request.args.get('q')
            if q:
                query = query.filter(
                    or_(
                        ActivityLog.user_id.ilike(f"%{q}%"),
                        ActivityLog.action.ilike(f"%{q}%"),
                        ActivityLog.details.ilike(f"%{q}%"),
                        ActivityLog.ip_address.ilike(f"%{q}%"),
                    )
                )

            total_records = query.count()

            if page is not None and limit is not None:
                if page < 1: page = 1
                if limit < 1: limit = 10
                query = query.offset((page - 1) * limit).limit(limit)
            else:
                # If no pagination, return all records
                page = 1
                limit = total_records

            logs = query.all()
            result = activity_logs_serializers.dump(logs)

            # 🔹 Structured response
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
