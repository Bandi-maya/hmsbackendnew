import json
import logging
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from new import with_tenant_session_and_user
from utils.logger import log_activity

from Models.SurgeryDoctor import SurgeryDoctor
from Serializers.SurgeryDoctorSerializers import surgery_doctor_serializer, surgery_doctor_serializers

logger = logging.getLogger(__name__)

class SurgeryDoctorResource(Resource):
    method_decorators = [jwt_required()]

    # ✅ GET single or all surgery-doctor assignments
    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            sd_id = request.args.get('id')
            if sd_id:
                record = tenant_session.query(SurgeryDoctor).get(sd_id)
                if not record:
                    return {"error": "SurgeryDoctor record not found"}, 404
                return surgery_doctor_serializer.dump(record), 200

            records = tenant_session.query(SurgeryDoctor).all()
            return surgery_doctor_serializers.dump(records), 200

        except Exception:
            logger.exception("Error fetching SurgeryDoctor records")
            return {"error": "Internal error occurred"}, 500

    # ✅ POST new assignment
    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            surgery_id = json_data.get('surgery_id')
            doctor_id = json_data.get('doctor_id')
            role = json_data.get('role')

            if not surgery_id or not doctor_id or not role:
                return {"error": "Missing required fields: surgery_id, doctor_id, role"}, 400

            existing = tenant_session.query(SurgeryDoctor).filter_by(
                surgery_id=surgery_id, doctor_id=doctor_id, role=role
            ).first()
            if existing:
                return {"error": "This doctor-role is already assigned to the surgery"}, 400

            SurgeryDoctor.tenant_session = tenant_session
            record = SurgeryDoctor(
                surgery_id=surgery_id,
                doctor_id=doctor_id,
                role=role
            )
            tenant_session.add(record)
            tenant_session.flush()
            tenant_session.commit()

            log_activity("CREATE_SURGERY_DOCTOR", details=json.dumps(surgery_doctor_serializer.dump(record)))

            return surgery_doctor_serializer.dump(record), 201

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error creating SurgeryDoctor record")
            return {"error": "Internal error occurred"}, 500

    # ✅ PUT update assignment
    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            sd_id = json_data.get('id')
            if not sd_id:
                return {"error": "SurgeryDoctor ID required"}, 400

            record = tenant_session.query(SurgeryDoctor).get(sd_id)
            if not record:
                return {"error": "SurgeryDoctor record not found"}, 404

            for field in ['surgery_id', 'doctor_id', 'role']:
                if field in json_data:
                    setattr(record, field, json_data[field])

            tenant_session.commit()
            log_activity("UPDATE_SURGERY_DOCTOR", details=json.dumps(surgery_doctor_serializer.dump(record)))

            return surgery_doctor_serializer.dump(record), 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error updating SurgeryDoctor record")
            return {"error": "Internal error occurred"}, 500

    # ✅ DELETE assignment
    @with_tenant_session_and_user
    def delete(self, tenant_session, **kwargs):
        try:
            sd_id = request.args.get('id')
            if not sd_id:
                return {"error": "SurgeryDoctor ID required"}, 400

            record = tenant_session.query(SurgeryDoctor).get(sd_id)
            if not record:
                return {"error": "SurgeryDoctor record not found"}, 404

            deleted_data = surgery_doctor_serializer.dump(record)
            tenant_session.delete(record)
            tenant_session.commit()

            log_activity("DELETE_SURGERY_DOCTOR", details=json.dumps(deleted_data))
            return {"message": "SurgeryDoctor record deleted successfully"}, 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error deleting SurgeryDoctor record")
            return {"error": "Internal error occurred"}, 500
