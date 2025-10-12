import json
import logging
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from Models.SurgeryType import SurgeryType
from Serializers.SurgeryTypeSerializers import surgery_type_serializer, surgery_type_serializers
from new import with_tenant_session_and_user
from utils.logger import log_activity

logger = logging.getLogger(__name__)

class SurgeryTypeResource(Resource):
    method_decorators = [jwt_required()]

    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            surgery_type_id = request.args.get('id')
            if surgery_type_id:
                surgery_type = tenant_session.query(SurgeryType).get(surgery_type_id)
                if not surgery_type:
                    return {"error": "Surgery Type not found"}, 404
                return surgery_type_serializer.dump(surgery_type), 200

            surgery_types = tenant_session.query(SurgeryType).all()
            result = surgery_type_serializers.dump(surgery_types)
            log_activity("GET_SURGERY_TYPES", details=json.dumps({"count": len(result)}))
            return result, 200

        except Exception:
            logger.exception("Error fetching surgery types")
            return {"error": "Internal error occurred"}, 500

    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            name = json_data.get('name')
            department_id = json_data.get('department_id')
            description = json_data.get('description')

            if not name or not department_id:
                return {"error": "Missing required fields: name, department_id"}, 400

            existing = tenant_session.query(SurgeryType).filter_by(name=name, department_id=department_id).first()
            if existing:
                return {"error": f"Surgery Type '{name}' already exists in this department"}, 400

            SurgeryType.tenant_session = tenant_session
            surgery_type = SurgeryType(
                name=name,
                department_id=department_id,
                description=description
            )
            tenant_session.add(surgery_type)
            tenant_session.commit()

            log_activity("CREATE_SURGERY_TYPE", details=json.dumps(surgery_type_serializer.dump(surgery_type)))

            return surgery_type_serializer.dump(surgery_type), 201

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error creating surgery type")
            return {"error": "Internal error occurred"}, 500

    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            surgery_type_id = json_data.get('id')
            if not surgery_type_id:
                return {"error": "Surgery Type ID required"}, 400

            surgery_type = tenant_session.query(SurgeryType).get(surgery_type_id)
            if not surgery_type:
                return {"error": "Surgery Type not found"}, 404

            for key in ['name', 'department_id', 'description']:
                if key in json_data:
                    setattr(surgery_type, key, json_data[key])

            tenant_session.commit()

            log_activity("UPDATE_SURGERY_TYPE", details=json.dumps(surgery_type_serializer.dump(surgery_type)))

            return surgery_type_serializer.dump(surgery_type), 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error updating surgery type")
            return {"error": "Internal error occurred"}, 500

    @with_tenant_session_and_user
    def delete(self, tenant_session, **kwargs):
        try:
            surgery_type_id = request.args.get('id')
            if not surgery_type_id:
                return {"error": "Surgery Type ID required"}, 400

            surgery_type = tenant_session.query(SurgeryType).get(surgery_type_id)
            if not surgery_type:
                return {"error": "Surgery Type not found"}, 404

            deleted_data = surgery_type_serializer.dump(surgery_type)
            tenant_session.delete(surgery_type)
            tenant_session.commit()

            log_activity("DELETE_SURGERY_TYPE", details=json.dumps(deleted_data))

            return {"message": "Surgery Type deleted successfully"}, 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error deleting surgery type")
            return {"error": "Internal error occurred"}, 500
