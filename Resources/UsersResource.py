# import requests
import string
import random

from flask import request, g
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from werkzeug.security import generate_password_hash

from Models.UserExtraFields import UserExtraFields
from Models.UserField import UserField
from Models.UserType import UserType
from Models.Users import User
from Serializers.UserSerializers import user_serializers, user_serializer
from new import with_tenant_session_and_user
from extentions import db
from utils.utils import send_email


def generate_random_password(length=10):
    chars = string.ascii_letters + string.digits + """!#$%&()*+,-.:;<=>?@[]_{}"""
    return ''.join(random.choice(chars) for _ in range(length))

class UsersResource(Resource):
    method_decorators = [jwt_required()]

    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            user_type = g.user.get('user_type', {}).get('type') if hasattr(g, "user") and g.user else None

            query = tenant_session.query(User).filter_by(is_deleted=False)
            user_id = request.args.get('user_id', type=int)
            department_id = request.args.get('department_id')
            req_user_type = request.args.get('user_type')

            # 🔹 Role-based filters
            if user_type == 'Admin':
                pass
            elif user_type == 'Patient':
                query = query.filter(User.id == g.user.get('id'))
            elif g.user and g.user.get('department_id'):
                query = query.filter(User.department_id == g.user.get('department_id'))

            # 🔹 Filter by user_id
            if user_id:
                user = query.filter(User.id == user_id).first()
                if not user:
                    return {"message": "User not found"}, 404
                return user_serializer.dump(user), 200

            # 🔹 Filter by department_id
            if department_id:
                query = query.filter(User.department_id == department_id)

            # 🔹 Filter by user_type
            if req_user_type:
                query = query.join(UserType).filter(func.upper(UserType.type) == req_user_type.upper())

            # 🔹 Pagination parameters
            page = request.args.get("page", type=int)
            limit = request.args.get("limit", type=int)

            total_records = query.count()

            # 🔹 Apply pagination only if both page and limit are provided
            if page is not None and limit is not None:
                if page < 1: page = 1
                if limit < 1: limit = 10
                query = query.offset((page - 1) * limit).limit(limit)
            else:
                # If page or limit not provided, return all users
                page = 1
                limit = total_records

            users = query.all()

            # 🔹 Response structure
            return {
                "page": page,
                "limit": limit,
                "total_records": total_records,
                "total_pages": (total_records + limit - 1) // limit if limit else 1,
                "data": user_serializers.dump(users)
            }, 200

        except Exception as e:
            print("Error in GET /user:", e)
            return {"message": "Internal error occurred"}, 500

    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"message": "No input data provided"}, 400

            extra_fields_data = json_data.pop('extra_fields', {})
            user_type_id = json_data.get('user_type_id')
            if not user_type_id:
                return {"message": "No user_type_id provided"}, 400

            # This logic assumes you have a utility function for sending email
            random_password = generate_random_password()
            json_data['password'] = generate_password_hash(random_password)

            User.tenant_session = tenant_session
            user = User(**json_data)
            tenant_session.add(user)
            tenant_session.flush()  # flush to get the user.id for the extra fields

            send_email("Your Account Password", [user.email], f"Your password is: {random_password}")

            fields = tenant_session.query(UserField).filter_by(user_type=user_type_id).all()
            for field in fields:
                if field.is_mandatory and not extra_fields_data.get(field.field_name):
                    return {"message": f"{field.field_name} is missing in extra fields."}, 400

            tenant_session.add(UserExtraFields(
                user_id=user.id,
                fields_data=extra_fields_data
            ))

            tenant_session.commit()
            return user_serializer.dump(user), 201
        except IntegrityError as ie:
            tenant_session.rollback()
            return {"message": f"Database integrity error: {str(ie.orig)}"}, 400
        except Exception as e:
            tenant_session.rollback()
            print(e)
            return {"message": "Internal server error"}, 500

    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"message": "No input data provided"}, 400

            user_id = json_data.get("id")
            if not user_id:
                return {"message": "User ID is required for update"}, 400

            user = tenant_session.query(User).get(user_id)
            if not user:
                return {"message": "User not found"}, 404

            for key, value in json_data.items():
                if hasattr(user, key) and key not in ["extra_fields", "id"]:
                    setattr(user, key, value)

            extra_fields_data = json_data.get('extra_fields', {})
            if extra_fields_data:
                user_extra_fields = tenant_session.query(UserExtraFields).filter_by(user_id=user_id).first()
                if user_extra_fields:
                    user_extra_fields.fields_data = {**user_extra_fields.fields_data, **extra_fields_data}
                else:
                    UserExtraFields.tenant_session = tenant_session
                    tenant_session.add(UserExtraFields(user_id=user.id, fields_data=extra_fields_data))

            tenant_session.commit()
            return user_serializer.dump(user), 200
        except Exception as e:
            tenant_session.rollback()
            print(e)
            return {"message": "Internal server error"}, 500

    @with_tenant_session_and_user
    def delete(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            user_id = json_data.get("id")
            if not user_id:
                return {"message": "User ID is required for delete"}, 400

            user = tenant_session.query(User).get(user_id)
            if not user:
                return {"message": "User not found"}, 404

            # Soft delete
            user.is_deleted = True
            user.is_active = False

            tenant_session.commit()
            return {"message": "User deleted successfully"}, 200
        except Exception as e:
            tenant_session.rollback()
            print(e)
            return {"message": "Internal server error"}, 50