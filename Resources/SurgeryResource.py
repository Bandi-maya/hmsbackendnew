from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import logging
import json

from Models.Surgery import Surgery
from Serializers.SurgerySerializers import surgery_serializer, surgery_serializers
from new import with_tenant_session_and_user
from utils.logger import log_activity

logger = logging.getLogger(__name__)

class SurgeryResource(Resource):
    method_decorators = [jwt_required()]

    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            surgery_id = request.args.get('id')
            if surgery_id:
                surgery = tenant_session.query(Surgery).get(surgery_id)
                if not surgery:
                    return {"error": "Surgery not found"}, 404
                return surgery_serializer.dump(surgery), 200

            surgeries = tenant_session.query(Surgery).all()
            result = surgery_serializers.dump(surgeries)
            log_activity("GET_SURGERIES", details=json.dumps({"count": len(result)}))
            return result, 200

        except Exception:
            logger.exception("Error fetching surgeries")
            return {"error": "Internal error occurred"}, 500

    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            patient_id = json_data.get('patient_id')
            surgery_type_id = json_data.get('surgery_type_id')
            scheduled_start_time = json_data.get('scheduled_start_time')

            if not patient_id or not surgery_type_id or not scheduled_start_time:
                return {"error": "Missing required fields: patient_id, surgery_type_id, scheduled_start_time"}, 400

            try:
                scheduled_start_dt = datetime.fromisoformat(scheduled_start_time)
            except Exception:
                return {"error": "Invalid format for scheduled_start_time. Use ISO format."}, 400

            scheduled_end_time = json_data.get('scheduled_end_time')
            scheduled_end_dt = None
            if scheduled_end_time:
                try:
                    scheduled_end_dt = datetime.fromisoformat(scheduled_end_time)
                except Exception:
                    return {"error": "Invalid format for scheduled_end_time. Use ISO format."}, 400

            surgery = Surgery(
                patient_id=patient_id,
                surgery_type_id=surgery_type_id,
                operation_theatre_id=json_data.get('operation_theatre_id'),
                scheduled_start_time=scheduled_start_dt,
                scheduled_end_time=scheduled_end_dt,
                actual_start_time=None,
                actual_end_time=None,
                status=json_data.get('status', 'Scheduled'),
                notes=json_data.get('notes')
            )

            tenant_session.add(surgery)
            tenant_session.flush()
            tenant_session.commit()

            log_activity("CREATE_SURGERY", details=surgery_serializer.dump(surgery))
            return surgery_serializer.dump(surgery), 201

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": str(ie.orig)}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error creating surgery")
            return {"error": "Internal error occurred"}, 500

    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            surgery_id = json_data.get('id')
            if not surgery_id:
                return {"error": "Surgery ID required"}, 400

            surgery = tenant_session.query(Surgery).get(surgery_id)
            if not surgery:
                return {"error": "Surgery not found"}, 404

            # Update fields if present
            for key in ['patient_id', 'surgery_type_id', 'operation_theatre_id', 'status', 'notes']:
                if key in json_data:
                    setattr(surgery, key, json_data[key])

            for dt_field in ['scheduled_start_time', 'scheduled_end_time', 'actual_start_time', 'actual_end_time']:
                if dt_field in json_data and json_data[dt_field]:
                    try:
                        setattr(surgery, dt_field, datetime.fromisoformat(json_data[dt_field]))
                    except Exception:
                        return {"error": f"Invalid format for {dt_field}. Use ISO format."}, 400

            tenant_session.commit()
            log_activity("UPDATE_SURGERY", details=surgery_serializer.dump(surgery))
            return surgery_serializer.dump(surgery), 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": str(ie.orig)}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error updating surgery")
            return {"error": "Internal error occurred"}, 500

    @with_tenant_session_and_user
    def delete(self, tenant_session, **kwargs):
        try:
            surgery_id = request.args.get('id')
            if not surgery_id:
                return {"error": "Surgery ID required"}, 400

            surgery = tenant_session.query(Surgery).get(surgery_id)
            if not surgery:
                return {"error": "Surgery not found"}, 404

            deleted_data = surgery_serializer.dump(surgery)
            tenant_session.delete(surgery)
            tenant_session.commit()

            log_activity("DELETE_SURGERY", details=deleted_data)
            return {"message": "Surgery deleted successfully"}, 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": str(ie.orig)}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error deleting surgery")
            return {"error": "Internal error occurred"}, 500
