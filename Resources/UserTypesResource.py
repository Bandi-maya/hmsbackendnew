from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
import logging

from Models.UserType import UserType
from Models.Users import User
from Serializers.UserTypeSerializer import user_type_serializers, user_type_serializer
from new import with_tenant_session_and_user
from extentions import db

logger = logging.getLogger(__name__)

class UserTypesResource(Resource):
    method_decorators = [jwt_required()]

    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            # 🔹 Optional filter
            name = request.args.get("name")

            query = tenant_session.query(UserType).filter_by(is_active=True)

            if name:
                query = query.filter(UserType.type.ilike(f"%{name}%"))

            total_records = query.count()

            # 🔹 Pagination params (optional)
            page = request.args.get("page", type=int) or 1
            limit = request.args.get("limit", type=int) or total_records if total_records > 0 else 1

            if page < 1:
                page = 1
            if limit < 1:
                limit = 10

            # 🔹 Apply pagination
            user_types = query.offset((page - 1) * limit).limit(limit).all()
            result = user_type_serializer.dump(user_types)

            # 🔹 Structured response
            response = {
                "page": page,
                "page_size": limit,
                "total_records": total_records,
                "total_pages": (total_records + limit - 1) // limit,
                "data": result
            }

            return response, 200

        except Exception as e:
            print(f"Error fetching user types: {e}")
            return {"message": "Internal error occurred"}, 500

    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"message": "No input data provided"}, 400

            UserType.tenant_session = tenant_session
            new_user_type = UserType(**json_data)
            tenant_session.add(new_user_type)
            tenant_session.commit()

            return user_type_serializer.dump(new_user_type), 201
        except IntegrityError as ie:
            tenant_session.rollback()
            return {"message": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            print(f"Error creating user type: {e}")
            return {"message": "Internal error occurred"}, 500

    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"message": "No input data provided"}, 400

            user_type_id = json_data.get("id")
            if not user_type_id:
                return {"message": "User Type ID is required for update"}, 400

            user_type = tenant_session.query(UserType).get(user_type_id)
            if not user_type:
                return {"message": "User Type not found"}, 404

            for key, value in json_data.items():
                if hasattr(user_type, key):
                    setattr(user_type, key, value)

            tenant_session.commit()
            return user_type_serializer.dump(user_type), 200
        except IntegrityError as ie:
            tenant_session.rollback()
            return {"message": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            print(f"Error updating user type: {e}")
            return {"message": "Internal error occurred"}, 500

    @with_tenant_session_and_user
    def delete(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            user_type_id = json_data.get("id")
            if not user_type_id:
                return {"message": "User Type ID is required for delete"}, 400

            user_type = tenant_session.query(UserType).get(user_type_id)
            if not user_type:
                return {"message": "User Type not found"}, 404

            user = tenant_session.query(User).filter_by(user_type_id=user_type.id, is_active=True, is_deleted=False).first()
            if user:
                return {"message": "User Type cannot be deleted as a user is assigned to it"}, 400

            user_type.is_active = False
            user_type.is_deleted = True
            tenant_session.commit()

            return {"message": "User type deactivated successfully"}, 200
        except Exception as e:
            tenant_session.rollback()
            print(f"Error deleting user type: {e}")
            return {"message": "Internal error occurred"}, 500
