from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import logging

from Models.Tokens import Token
from Serializers.TokenSerializers import TokenSerializers, TokenSerializerz
from new import with_tenant_session_and_user

logger = logging.getLogger(__name__)

class TokenResource(Resource):
    method_decorators = [jwt_required()]

    # ✅ GET tokens
    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            department_id = request.args.get("department_id")
            date = request.args.get("date")
            doctor_id = request.args.get("doctor_id")

            query = tenant_session.query(Token)

            if doctor_id:
                query = query.filter_by(doctor_id=doctor_id)
            if department_id:
                query = query.filter_by(department_id=department_id)
            if date:
                try:
                    date_obj = datetime.strptime(date, "%Y-%m-%d")
                    query = query.filter(Token.appointment_date == date_obj)
                except Exception:
                    return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400

            tokens = query.all()
            return TokenSerializers.dump(tokens, many=True), 200

        except Exception:
            logger.exception("Error fetching tokens")
            return {"error": "Internal error occurred"}, 500

    # ✅ POST create token
    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            token = Token(**json_data)
            tenant_session.add(token)
            tenant_session.commit()

            return TokenSerializerz.dump(token), 201

        except ValueError as ve:
            tenant_session.rollback()
            return {"error": str(ve)}, 400
        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error creating token")
            return {"error": "Internal error occurred"}, 500

    # ✅ PUT update token
    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            token_id = json_data.get("id")
            if not token_id:
                return {"error": "Token ID is required for update"}, 400

            token = tenant_session.query(Token).get(token_id)
            if not token:
                return {"error": "Token not found"}, 404

            for key, value in json_data.items():
                if hasattr(token, key):
                    setattr(token, key, value)

            tenant_session.commit()
            return TokenSerializerz.dump(token), 200

        except ValueError as ve:
            tenant_session.rollback()
            return {"error": str(ve)}, 400
        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error updating token")
            return {"error": "Internal error occurred"}, 500

    # ✅ DELETE token
    @with_tenant_session_and_user
    def delete(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            token_id = json_data.get("id")
            if not token_id:
                return {"error": "Token ID is required for deletion"}, 400

            token = tenant_session.query(Token).get(token_id)
            if not token:
                return {"error": "Token not found"}, 404

            tenant_session.delete(token)
            tenant_session.commit()
            return {"message": "Token deleted successfully"}, 200

        except Exception:
            tenant_session.rollback()
            logger.exception("Error deleting token")
            return {"error": "Internal error occurred"}, 500
