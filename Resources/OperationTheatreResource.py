from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
import logging

from Models.OperationTheatre import OperationTheatre
from Serializers.OperationTheatreSerializers import operation_theatre_serializer, operation_theatre_serializers
from new import with_tenant_session_and_user
from utils.logger import log_activity

logger = logging.getLogger(__name__)

class OperationTheatreResource(Resource):
    method_decorators = [jwt_required()]

    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            theatre_id = request.args.get('id')
            if theatre_id:
                theatre = tenant_session.query(OperationTheatre).get(theatre_id)
                if not theatre:
                    return {"error": "Operation Theatre not found"}, 404
                return operation_theatre_serializer.dump(theatre), 200

            theatres = tenant_session.query(OperationTheatre).all()
            result = operation_theatre_serializers.dump(theatres)
            log_activity("GET_OPERATION_THEATRES", details={"count": len(result)})
            return result, 200

        except Exception:
            logger.exception("Error fetching operation theatres")
            return {"error": "Internal error occurred"}, 500

    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            name = json_data.get('name')
            department_id = json_data.get('department_id')
            if not name or not department_id:
                return {"error": "Missing required fields: name, department_id"}, 400

            existing_ot = tenant_session.query(OperationTheatre).filter_by(name=name).first()
            if existing_ot:
                return {"error": f"Operation Theatre with name '{name}' already exists"}, 400

            theatre = OperationTheatre(
                name=name,
                building=json_data.get('building'),
                floor=json_data.get('floor'),
                wing=json_data.get('wing'),
                room_number=json_data.get('room_number'),
                department_id=department_id,
                status=json_data.get('status', 'Available'),
                is_active=json_data.get('is_active', True),
                notes=json_data.get('notes')
            )
            tenant_session.add(theatre)
            tenant_session.flush()
            tenant_session.commit()

            log_activity("CREATE_OPERATION_THEATRE", details=operation_theatre_serializer.dump(theatre))
            return operation_theatre_serializer.dump(theatre), 201

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": str(ie.orig)}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error creating operation theatre")
            return {"error": "Internal error occurred"}, 500

    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            theatre_id = json_data.get('id')
            if not theatre_id:
                return {"error": "Operation Theatre ID required"}, 400

            theatre = tenant_session.query(OperationTheatre).get(theatre_id)
            if not theatre:
                return {"error": "Operation Theatre not found"}, 404

            for key in ['name', 'building', 'floor', 'wing', 'room_number', 'department_id', 'status', 'is_active', 'notes']:
                if key in json_data:
                    setattr(theatre, key, json_data.get(key))

            tenant_session.commit()
            log_activity("UPDATE_OPERATION_THEATRE", details=operation_theatre_serializer.dump(theatre))
            return operation_theatre_serializer.dump(theatre), 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": str(ie.orig)}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error updating operation theatre")
            return {"error": "Internal error occurred"}, 500

    @with_tenant_session_and_user
    def delete(self, tenant_session, **kwargs):
        try:
            theatre_id = request.args.get('id')
            if not theatre_id:
                return {"error": "Operation Theatre ID required"}, 400

            theatre = tenant_session.query(OperationTheatre).get(theatre_id)
            if not theatre:
                return {"error": "Operation Theatre not found"}, 404

            deleted_data = operation_theatre_serializer.dump(theatre)
            tenant_session.delete(theatre)
            tenant_session.commit()

            log_activity("DELETE_OPERATION_THEATRE", details=deleted_data)
            return {"message": "Operation Theatre deleted successfully"}, 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": str(ie.orig)}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error deleting operation theatre")
            return {"error": "Internal error occurred"}, 500
