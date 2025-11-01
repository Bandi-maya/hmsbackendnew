from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
import logging

from Models.LabReport import LabReport
from Models.PurchaseTest import PurchaseTest
from Serializers.LabReportSerializers import lab_report_serializer, lab_report_serializers
from Serializers.PurchaseTestSerializers import purchase_test_serializer
from new import with_tenant_session_and_user  # Tenant session decorator
from utils.logger import log_activity

logger = logging.getLogger(__name__)


class LabReportsResource(Resource):
    method_decorators = [jwt_required()]

    # ✅ GET all lab reports
    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            # 🔹 Base query
            query = tenant_session.query(LabReport)
            total_records = query.count()

            # 🔹 Pagination params (optional)
            page = request.args.get("page", type=int)
            limit = request.args.get("limit", type=int)

            q = request.args.get('q')
            if q:
                query = query.filter(
                    or_(
                        LabReport.request_id.ilike(f"%{q}%"),
                        LabReport.report_data.ilike(f"%{q}%"),
                    )
                )

            # 🔹 Apply pagination if both page and limit are provided
            if page is not None and limit is not None:
                if page < 1: page = 1
                if limit < 1: limit = 10
                query = query.offset((page - 1) * limit).limit(limit)
            else:
                # Return all if pagination not provided
                page = 1
                limit = total_records

            reports = query.all()
            result = lab_report_serializers.dump(reports)

            # 🔹 Log activity
            log_activity(
                "GET_LAB_REPORTS",
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
            logger.exception("Error fetching lab reports")
            return {"error": "Internal error occurred"}, 500

    # # ✅ POST create new lab report
    # @with_tenant_session_and_user
    # def post(self, tenant_session, **kwargs):
    #     try:
    #         json_data = request.get_json(force=True)
    #         if not json_data:
    #             return {"error": "No input data provided"}, 400

    #         request_id = json_data.get("request_id")
    #         if not tenant_session.query(PurchaseTest).get(request_id):
    #             return {"error": "LabRequest not found"}, 404

    #         PurchaseTest.tenant_session = tenant_session
    #         lab_report = PurchaseTest(**json_data)
    #         tenant_session.add(lab_report)
    #         tenant_session.commit()
    #         return lab_report_serializer.dump(lab_report), 201

    #     except IntegrityError as ie:
    #         tenant_session.rollback()
    #         return {"error": f"Database integrity error: {ie.orig}"}, 400
    #     except Exception as e:
    #         tenant_session.rollback()
    #         logger.exception("Error creating lab report")
    #         return {"error": "Internal error occurred"}, 500

    # ✅ PUT update existing lab report
    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            report_id = json_data.get("id")
            if not report_id:
                return {"error": "LabReport ID required"}, 400

            lab_report = tenant_session.query(PurchaseTest).get(report_id)
            if not lab_report:
                return {"error": "LabReport not found"}, 404

            for key, value in json_data.items():
                if hasattr(lab_report, key):
                    setattr(lab_report, key, value)

            tenant_session.commit()
            return purchase_test_serializer.dump(lab_report), 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error updating lab report")
            return {"error": "Internal error occurred"}, 500

    # # ✅ DELETE a lab report
    # @with_tenant_session_and_user
    # def delete(self, tenant_session, **kwargs):
    #     try:
    #         report_id = request.args.get("id")
    #         if not report_id:
    #             return {"error": "LabReport ID required"}, 400

    #         lab_report = tenant_session.query(LabReport).get(report_id)
    #         if not lab_report:
    #             return {"error": "LabReport not found"}, 404

    #         tenant_session.delete(lab_report)
    #         tenant_session.commit()
    #         return {"message": "LabReport deleted successfully"}, 200

    #     except IntegrityError as ie:
    #         tenant_session.rollback()
    #         return {"error": f"Database integrity error: {ie.orig}"}, 400
    #     except Exception as e:
    #         tenant_session.rollback()
    #         logger.exception("Error deleting lab report")
    #         return {"error": "Internal error occurred"}, 500
