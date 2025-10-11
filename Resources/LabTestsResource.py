from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
import logging

from Models.LabTest import LabTest
from Serializers.LabTestSerializers import lab_test_serializer, lab_test_serializers
from new import with_tenant_session_and_user  # Tenant session decorator

logger = logging.getLogger(__name__)


class LabTestsResource(Resource):
    method_decorators = [jwt_required()]

    # ✅ GET all lab tests
    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            tests = tenant_session.query(LabTest).all()
            return lab_test_serializers.dump(tests), 200
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

    # ✅ PUT update an existing lab test
    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            test_id = json_data.get("id")
            if not test_id:
                return {"error": "LabTest ID required"}, 400

            lab_test = tenant_session.query(LabTest).get(test_id)
            if not lab_test:
                return {"error": "LabTest not found"}, 404

            for key, value in json_data.items():
                if hasattr(lab_test, key):
                    setattr(lab_test, key, value)

            tenant_session.commit()
            return lab_test_serializer.dump(lab_test), 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error updating lab test")
            return {"error": "Internal error occurred"}, 500

    # ✅ DELETE a lab test
    @with_tenant_session_and_user
    def delete(self, tenant_session, **kwargs):
        try:
            test_id = request.args.get("id")
            if not test_id:
                return {"error": "LabTest ID required"}, 400

            lab_test = tenant_session.query(LabTest).get(test_id)
            if not lab_test:
                return {"error": "LabTest not found"}, 404

            tenant_session.delete(lab_test)
            tenant_session.commit()
            return {"message": "LabTest deleted successfully"}, 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error deleting lab test")
            return {"error": "Internal error occurred"}, 500
