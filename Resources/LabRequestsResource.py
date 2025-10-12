from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
import logging

from Models.LabRequest import LabRequest
from Models.Users import User
from Models.LabTest import LabTest
from Serializers.LabRequestSerializers import lab_request_serializer, lab_request_serializers
from new import with_tenant_session_and_user  # Tenant session decorator
from utils.logger import log_activity

logger = logging.getLogger(__name__)


class LabRequestsResource(Resource):
    method_decorators = [jwt_required()]

    # ✅ GET all lab requests
    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            # 🔹 Base query
            query = tenant_session.query(LabRequest)
            total_records = query.count()

            # 🔹 Pagination params (optional)
            page = request.args.get("page", type=int)
            limit = request.args.get("limit", type=int)

            # 🔹 Apply pagination if both page and limit are provided
            if page is not None and limit is not None:
                if page < 1: page = 1
                if limit < 1: limit = 10
                query = query.offset((page - 1) * limit).limit(limit)
            else:
                # Return all if pagination not provided
                page = 1
                limit = total_records

            lab_requests = query.all()
            result = lab_request_serializers.dump(lab_requests)

            # 🔹 Log activity
            log_activity(
                "GET_LAB_REQUESTS",
                details={"count": len(result), "page": page, "limit": limit}
            )

            # 🔹 Structured response
            return {
                "page": page,
                "limit": limit,
                "total_records": total_records,
                "total_pages": (total_records + limit - 1) // limit if limit else 1,
                "data": result
            }, 200

        except Exception:
            logger.exception("Error fetching lab requests")
            return {"error": "Internal error occurred"}, 500

    # ✅ POST create new lab request(s)
    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            patient_id = json_data.get("patient_id")
            if not tenant_session.query(User).get(patient_id):
                return {"error": "Patient not found"}, 404

            test_ids = json_data.get("test_id")
            if isinstance(test_ids, list):
                del json_data["test_id"]
                for test_id in test_ids:
                    if not tenant_session.query(LabTest).get(test_id):
                        return {"error": f"LabTest ID {test_id} not found"}, 404

                    LabRequest.tenant_session = tenant_session
                    lab_request = LabRequest(**json_data, test_id=test_id)
                    tenant_session.add(lab_request)
                tenant_session.commit()
                return {"status": "success"}, 201
            else:
                if not tenant_session.query(LabTest).get(test_ids):
                    return {"error": "LabTest not found"}, 404
                lab_request = LabRequest(**json_data)
                tenant_session.add(lab_request)
                tenant_session.commit()
                return lab_request_serializer.dump(lab_request), 201

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error creating lab request")
            return {"error": "Internal error occurred"}, 500

    # ✅ PUT update an existing lab request
    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            request_id = json_data.get("id")
            if not request_id:
                return {"error": "LabRequest ID required"}, 400

            lab_request = tenant_session.query(LabRequest).get(request_id)
            if not lab_request:
                return {"error": "LabRequest not found"}, 404

            for key, value in json_data.items():
                if hasattr(lab_request, key):
                    setattr(lab_request, key, value)

            tenant_session.commit()
            return lab_request_serializer.dump(lab_request), 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error updating lab request")
            return {"error": "Internal error occurred"}, 500

    # ✅ DELETE a lab request
    @with_tenant_session_and_user
    def delete(self, tenant_session, **kwargs):
        try:
            request_id = request.args.get("id")
            if not request_id:
                return {"error": "LabRequest ID required"}, 400

            lab_request = tenant_session.query(LabRequest).get(request_id)
            if not lab_request:
                return {"error": "LabRequest not found"}, 404

            tenant_session.delete(lab_request)
            tenant_session.commit()
            return {"message": "LabRequest deleted successfully"}, 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error deleting lab request")
            return {"error": "Internal error occurred"}, 500
