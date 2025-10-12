from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
import logging

from Models.MedicalRecords import MedicalRecords
from Models.Users import User
from Serializers.MedicalRecordsSerializer import medical_records_serializers, medical_records_serializer
from new import with_tenant_session_and_user

logger = logging.getLogger(__name__)


class MedicalRecordsResource(Resource):
    method_decorators = [jwt_required()]

    # ✅ GET all medical records
    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            records = tenant_session.query(MedicalRecords).all()
            return medical_records_serializers.dump(records), 200
        except Exception as e:
            logger.exception("Error fetching medical records")
            return {"error": "Internal error occurred"}, 500

    # ✅ POST create new medical record
    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            user_id = json_data.get("user_id")
            if not user_id:
                return {"error": "User ID is required"}, 400

            user = tenant_session.query(User).get(user_id)
            if not user:
                return {"error": f"User ID {user_id} not found"}, 404

            # Create new record
            MedicalRecords.tenant_session = tenant_session
            medical_record = MedicalRecords(**json_data)
            tenant_session.add(medical_record)
            tenant_session.commit()

            return medical_records_serializer.dump(medical_record), 201

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except ValueError as ve:
            tenant_session.rollback()
            return {"error": str(ve)}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error creating medical record")
            return {"error": "Internal error occurred"}, 500

    # ✅ PUT update medical record
    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            record_id = json_data.get("id")
            if not record_id:
                return {"error": "Medical Record ID required"}, 400

            medical_record = tenant_session.query(MedicalRecords).get(record_id)
            if not medical_record:
                return {"error": "Medical Record not found"}, 404

            # Update editable fields
            for key, value in json_data.items():
                if hasattr(medical_record, key):
                    setattr(medical_record, key, value)

            tenant_session.commit()
            return medical_records_serializer.dump(medical_record), 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error updating medical record")
            return {"error": "Internal error occurred"}, 500

    # ✅ DELETE (soft restriction)
    @with_tenant_session_and_user
    def delete(self, tenant_session, **kwargs):
        # Currently not supporting deletion
        return {"error": "Now we are not supporting deletion of Medical Records"}, 400

        # The below code can be enabled in future if needed
        """
        try:
            record_id = request.args.get("id")
            if not record_id:
                return {"error": "Medical Record ID required"}, 400

            record = tenant_session.query(MedicalRecords).get(record_id)
            if not record:
                return {"error": "Medical Record not found"}, 404

            tenant_session.delete(record)
            tenant_session.commit()
            return {"message": "Medical Record deleted successfully"}, 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error deleting medical record")
            return {"error": "Internal error occurred"}, 500
        """
