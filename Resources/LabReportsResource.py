from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
import logging

from Models.LabReport import LabReport
from Models.LabRequest import LabRequest
from Serializers.LabReportSerializers import lab_report_serializer, lab_report_serializers
from new import with_tenant_session_and_user  # Tenant session decorator

logger = logging.getLogger(__name__)


class LabReportsResource(Resource):
    method_decorators = [jwt_required()]

    # ✅ GET all lab reports
    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            reports = tenant_session.query(LabReport).all()
            return lab_report_serializers.dump(reports), 200
        except Exception:
            logger.exception("Error fetching lab reports")
            return {"error": "Internal error occurred"}, 500

    # ✅ POST create new lab report
    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            request_id = json_data.get("request_id")
            if not tenant_session.query(LabRequest).get(request_id):
                return {"error": "LabRequest not found"}, 404

            lab_report = LabReport(**json_data)
            tenant_session.add(lab_report)
            tenant_session.commit()
            return lab_report_serializer.dump(lab_report), 201

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error creating lab report")
            return {"error": "Internal error occurred"}, 500

    # ✅ PUT update existing lab report
    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            report_id = json_data.get("id")
            if not report_id:
                return {"error": "LabReport ID required"}, 400

            lab_report = tenant_session.query(LabReport).get(report_id)
            if not lab_report:
                return {"error": "LabReport not found"}, 404

            for key, value in json_data.items():
                if hasattr(lab_report, key):
                    setattr(lab_report, key, value)

            tenant_session.commit()
            return lab_report_serializer.dump(lab_report), 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error updating lab report")
            return {"error": "Internal error occurred"}, 500

    # ✅ DELETE a lab report
    @with_tenant_session_and_user
    def delete(self, tenant_session, **kwargs):
        try:
            report_id = request.args.get("id")
            if not report_id:
                return {"error": "LabReport ID required"}, 400

            lab_report = tenant_session.query(LabReport).get(report_id)
            if not lab_report:
                return {"error": "LabReport not found"}, 404

            tenant_session.delete(lab_report)
            tenant_session.commit()
            return {"message": "LabReport deleted successfully"}, 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error deleting lab report")
            return {"error": "Internal error occurred"}, 500
