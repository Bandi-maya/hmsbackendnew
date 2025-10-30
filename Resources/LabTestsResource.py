from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy import or_, cast, String
from sqlalchemy.exc import IntegrityError
import logging

from Models.LabTest import LabTest
from Serializers.LabTestSerializers import lab_test_serializer, lab_test_serializers
from new import with_tenant_session_and_user  # Tenant session decorator
from utils.logger import log_activity

logger = logging.getLogger(__name__)


class LabTestsResource(Resource):
    method_decorators = [jwt_required()]

    # ✅ GET all lab tests
    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            # 🔹 Base query
            query = tenant_session.query(LabTest)

            # 🔹 Pagination params (optional)
            page = request.args.get("page", type=int)
            limit = request.args.get("limit", type=int)

            q = request.args.get('q')
            if q:
                query = query.filter(
                    or_(
                        LabTest.name.ilike(f"%{q}%"),
                        LabTest.description.ilike(f"%{q}%"),
                        cast(LabTest.price, String).ilike(f"%{q}%"),
                    )
                )
            status = request.args.get('status')
            if status is not None and status != '':
                print("status: ", status, status == 'true', status=='false')
                query = query.filter(
                    or_(
                        LabTest.is_available == True if status=='true' else False
                    )
                )

            total_records = query.count()

            # 🔹 Apply pagination if both page and limit are provided
            if page is not None and limit is not None:
                if page < 1: page = 1
                if limit < 1: limit = 10
                query = query.offset((page - 1) * limit).limit(limit)
            else:
                # Return all if pagination not provided
                page = 1
                limit = total_records

            tests = query.all()
            result = lab_test_serializers.dump(tests)

            # 🔹 Log activity
            log_activity(
                "GET_LAB_TESTS",
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
            logger.exception("Error fetching lab tests")
            return {"error": "Internal error occurred"}, 500

    # ✅ POST create a new lab test
    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            LabTest.tenant_session = tenant_session
            lab_test = LabTest(**json_data)
            tenant_session.add(lab_test)
            tenant_session.commit()

            return lab_test_serializer.dump(lab_test), 201

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error creating lab test")
            return {"error": str(e)}, 400

    # # ✅ PUT update an existing lab test
    # @with_tenant_session_and_user
    # def put(self, tenant_session, **kwargs):
    #     try:
    #         json_data = request.get_json(force=True)
    #         test_id = json_data.get("id")
    #         if not test_id:
    #             return {"error": "LabTest ID required"}, 400

    #         lab_test = tenant_session.query(LabTest).get(test_id)
    #         if not lab_test:
    #             return {"error": "LabTest not found"}, 404

    #         for key, value in json_data.items():
    #             if hasattr(lab_test, key):
    #                 setattr(lab_test, key, value)

    #         tenant_session.commit()
    #         return lab_test_serializer.dump(lab_test), 200

    #     except IntegrityError as ie:
    #         tenant_session.rollback()
    #         return {"error": f"Database integrity error: {ie.orig}"}, 400
    #     except Exception as e:
    #         tenant_session.rollback()
    #         logger.exception("Error updating lab test")
    #         return {"error": "Internal error occurred"}, 500

    # # ✅ DELETE a lab test
    # @with_tenant_session_and_user
    # def delete(self, tenant_session, **kwargs):
    #     try:
    #         test_id = request.args.get("id")
    #         if not test_id:
    #             return {"error": "LabTest ID required"}, 400

    #         lab_test = tenant_session.query(LabTest).get(test_id)
    #         if not lab_test:
    #             return {"error": "LabTest not found"}, 404

    #         tenant_session.delete(lab_test)
    #         tenant_session.commit()
    #         return {"message": "LabTest deleted successfully"}, 200

    #     except IntegrityError as ie:
    #         tenant_session.rollback()
    #         return {"error": f"Database integrity error: {ie.orig}"}, 400
    #     except Exception as e:
    #         tenant_session.rollback()
    #         logger.exception("Error deleting lab test")
    #         return {"error": "Internal error occurred"}, 500
