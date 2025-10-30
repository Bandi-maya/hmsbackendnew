from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy import or_, cast, String
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import logging

from sqlalchemy.orm import aliased

from Models.Tokens import Token
from Models.Users import User
from Serializers.TokenSerializers import TokenSerializers, TokenSerializerz
from new import with_tenant_session_and_user

logger = logging.getLogger(__name__)

class TokenResource(Resource):
    method_decorators = [jwt_required()]

    # ✅ GET tokens
    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            # 🔹 Query params
            department_id = request.args.get("department_id")
            date = request.args.get("date")
            doctor_id = request.args.get("doctor_id")
            status = request.args.get("status")

            # 🔹 Base query
            query = tenant_session.query(Token)

            # 🔹 Filters
            if doctor_id:
                query = query.filter_by(doctor_id=doctor_id)
            if department_id:
                query = query.filter_by(department_id=department_id)
            if date:
                try:
                    date_obj = datetime.strptime(date, "%Y-%m-%d")
                    query = query.filter(Token.appointment_date == date_obj)
                except ValueError:
                    return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400
            Doctor = aliased(User)
            Patient = aliased(User)
            query = query.join(Doctor, Token.doctor_id == Doctor.id).filter(~Doctor.is_deleted)
            query = query.join(Patient, Token.patient_id == Patient.id).filter(~Patient.is_deleted)
            total_records = query.count()
            scheduled_records = query.filter(Token.status == 'Alloted').count()
            completed_records = query.filter(Token.status == 'Completed').count()
            confirmed_records = query.filter(Token.status == 'Confirmed').count()
            pending_records = query.filter(Token.status == 'Pending').count()
            # 🔹 Pagination params
            page = request.args.get("page", type=int)
            limit = request.args.get("limit", type=int)
            q = request.args.get('q')
            if q:
                query = query.filter(
                    or_(
                        Doctor.name.ilike(f"%{q}%"),
                        Doctor.email.ilike(f"%{q}%"),
                        Patient.name.ilike(f"%{q}%"),
                        Patient.email.ilike(f"%{q}%"),
                        cast(Token.token_number, String).ilike(f"%{q}%"),
                    )
                )
            if status:
                query = query.filter(Token.status == status)


            # 🔹 Apply pagination only if both page and limit are provided
            if page is not None and limit is not None:
                if page < 1: page = 1
                if limit < 1: limit = 10
                query = query.offset((page - 1) * limit).limit(limit)
            else:
                # Return all tokens if pagination not provided
                page = 1
                limit = total_records

            tokens = query.all()
            result = TokenSerializers.dump(tokens, many=True)

            # 🔹 Structured response
            return {
                "page": page,
                "limit": limit,
                "alloted_records": scheduled_records,
                "completed_records": completed_records,
                "confirmed_records": confirmed_records,
                "pending_records": pending_records,
                "total_records": total_records,
                "total_pages": (total_records + limit - 1) // limit if limit else 1,
                "data": result
            }, 200

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

            Token.tenant_session = tenant_session
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

    # # ✅ DELETE token
    # @with_tenant_session_and_user
    # def delete(self, tenant_session, **kwargs):
    #     try:
    #         json_data = request.get_json(force=True)
    #         if not json_data:
    #             return {"error": "No input data provided"}, 400

    #         token_id = json_data.get("id")
    #         if not token_id:
    #             return {"error": "Token ID is required for deletion"}, 400

    #         token = tenant_session.query(Token).get(token_id)
    #         if not token:
    #             return {"error": "Token not found"}, 404

    #         tenant_session.delete(token)
    #         tenant_session.commit()
    #         return {"message": "Token deleted successfully"}, 200

    #     except Exception:
    #         tenant_session.rollback()
    #         logger.exception("Error deleting token")
    #         return {"error": "Internal error occurred"}, 500
