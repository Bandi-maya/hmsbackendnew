import string
import random
from datetime import datetime, timedelta

from flask import request, g
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from Models.UserExtraFields import UserExtraFields
from Models.UserField import UserField
from Models.UserType import UserType
from Models.Users import User
from Serializers.UserSerializers import user_serializers, user_serializer
from new import with_tenant_session_and_user
from utils.utils import send_email


# ---------------------------------------
# Utility: Generate Random Password
# ---------------------------------------
def generate_random_password(length=10):
    chars = string.ascii_letters + string.digits + "!#$%&()*+,-.:;<=>?@[]_{}"
    return ''.join(random.choice(chars) for _ in range(length))


# ---------------------------------------
# Users Resource
# ---------------------------------------
class UsersResource(Resource):
    method_decorators = [jwt_required()]

    # -----------------------------------
    # GET: List or Retrieve Users
    # -----------------------------------
    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            user_type = g.user.get('user_type', {}).get('type') if hasattr(g, "user") and g.user else None

            query = tenant_session.query(User).filter_by(is_deleted=False)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)

            # Filters
            user_id = request.args.get('user_id', type=int)
            department_id = request.args.get('department_id')
            req_user_type = request.args.get('user_type')
            q = request.args.get('q')

            # Role-based filtering
            if user_type == 'Admin':
                pass
            elif user_type == 'Patient':
                query = query.filter(User.id == g.user.get('id'))
            elif g.user and g.user.get('department_id'):
                query = query.filter(User.department_id == g.user.get('department_id'))

            # Filter by user_id (fetch single user)
            if user_id:
                user = query.filter(User.id == user_id).first()
                if not user:
                    return {"message": "User not found"}, 404
                return user_serializer.dump(user), 200

            # Filter by department
            if department_id:
                query = query.filter(User.department_id == department_id)

            # Join with user type
            query = query.join(UserType)

            # Count summaries
            patient_users_count = query.filter(func.upper(UserType.type) == 'PATIENT').count()
            doctor_users_count = query.filter(func.upper(UserType.type) == 'DOCTOR').count()
            nurse_users_count = query.filter(func.upper(UserType.type) == 'NURSE').count()
            staff_users_count = query.filter(~func.upper(UserType.type).in_(['NURSE', 'DOCTOR', 'PATIENT'])).count()

            # Filter by requested user_type
            if req_user_type:
                query = query.filter(func.upper(UserType.type) == req_user_type.upper())

            active_records = query.filter_by(is_active=True).count()
            recently_added_records = query.filter(
                User.is_deleted == False,
                User.created_at >= seven_days_ago
            ).count()

            # Search
            if q:
                query = query.filter(
                    or_(
                        User.name.ilike(f"%{q}%"),
                        User.email.ilike(f"%{q}%"),
                        User.username.ilike(f"%{q}%")
                    )
                )

            total_records = query.count()

            # Pagination
            page = request.args.get("page", type=int, default=1)
            limit = request.args.get("limit", type=int, default=10)
            if page < 1: page = 1
            if limit < 1: limit = 10

            query = query.offset((page - 1) * limit).limit(limit)
            users = query.all()

            # Response
            return {
                "page": page,
                "limit": limit,
                "recently_added": recently_added_records,
                "total_records": total_records,
                "patient_users_count": patient_users_count,
                "doctor_users_count": doctor_users_count,
                "nurse_users_count": nurse_users_count,
                "staff_users_count": staff_users_count,
                "active_records": active_records,
                "inactive_records": total_records - active_records,
                "total_pages": (total_records + limit - 1) // limit,
                "data": user_serializers.dump(users)
            }, 200

        except Exception as e:
            print("Error in GET /user:", e)
            return {"message": "Internal server error"}, 500

    # -----------------------------------
    # POST: Create a New User
    # -----------------------------------
    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"message": "No input data provided"}, 400

            extra_fields_data = json_data.pop('extra_fields', {})
            user_type_id = json_data.get('user_type_id')
            if not user_type_id:
                return {"message": "Missing user_type_id"}, 400

            # Generate and hash password
            random_password = generate_random_password()
            json_data['password'] = generate_password_hash(random_password)

            user = User(**json_data)
            tenant_session.add(user)
            tenant_session.flush()  # Get user.id

            # Send password via email
            send_email("Your Account Password", [user.email], f"Your password is: {random_password}")

            # Validate extra fields
            fields = tenant_session.query(UserField).filter_by(user_type=user_type_id).all()
            for field in fields:
                if field.is_mandatory and not extra_fields_data.get(field.field_name):
                    tenant_session.rollback()
                    return {"message": f"Missing mandatory field: {field.field_name}"}, 400

            tenant_session.add(UserExtraFields(user_id=user.id, fields_data=extra_fields_data))
            tenant_session.commit()

            return user_serializer.dump(user), 201

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"message": f"Database integrity error: {str(ie.orig)}"}, 400
        except Exception as e:
            tenant_session.rollback()
            print("Error in POST /user:", e)
            return {"message": "Internal server error"}, 500

    # -----------------------------------
    # PUT: Update Existing User
    # -----------------------------------
    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"message": "No input data provided"}, 400

            user_id = json_data.get("id")
            if not user_id:
                return {"message": "User ID is required"}, 400

            user = tenant_session.query(User).get(user_id)
            if not user:
                return {"message": "User not found"}, 404

            # Update user fields
            for key, value in json_data.items():
                if hasattr(user, key) and key not in ["extra_fields", "id"]:
                    setattr(user, key, value)

            # Handle extra fields
            extra_fields_data = json_data.get('extra_fields', {})
            if extra_fields_data:
                user_extra = tenant_session.query(UserExtraFields).filter_by(user_id=user_id).first()
                if user_extra:
                    user_extra.fields_data.update(extra_fields_data)
                else:
                    tenant_session.add(UserExtraFields(user_id=user.id, fields_data=extra_fields_data))

            tenant_session.commit()
            return user_serializer.dump(user), 200

        except Exception as e:
            tenant_session.rollback()
            print("Error in PUT /user:", e)
            return {"message": "Internal server error"}, 500

    # -----------------------------------
    # DELETE: Soft Delete User
    # -----------------------------------
    @with_tenant_session_and_user
    def delete(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data or not json_data.get("id"):
                return {"message": "User ID is required"}, 400

            user_id = json_data["id"]
            user = tenant_session.query(User).get(user_id)
            if not user:
                return {"message": "User not found"}, 404

            user.is_deleted = True
            user.is_active = False
            tenant_session.commit()

            return {"message": "User deleted successfully"}, 200

        except Exception as e:
            tenant_session.rollback()
            print("Error in DELETE /user:", e)
            return {"message": "Internal server error"}, 500
