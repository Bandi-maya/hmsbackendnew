from aniso8601.builders.python import year_range_check
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
import logging

from Models.UserField import UserField
from Models.UserExtraFields import UserExtraFields
from Models.Users import User
from Serializers.UserFieldSerializers import user_field_serializers, user_field_serializer
from new import with_tenant_session_and_user

logger = logging.getLogger(__name__)


class UserFieldsResource(Resource):
    method_decorators = [jwt_required()]

    # ✅ GET all user fields
    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            # 🔹 Optional filter
            field_name = request.args.get("name")
            query = tenant_session.query(UserField).filter_by(is_deleted=False)
            if field_name:
                query = query.filter(UserField.name.ilike(f"%{field_name}%"))

            # 🔹 Pagination params (optional)
            page = request.args.get("page", type=int)
            limit = request.args.get("limit", type=int)
            q = request.args.get('q')
            if q:
                query = query.filter(
                    or_(
                        UserField.field_name.ilike(f"%{q}%"),
                        UserField.field_type.ilike(f"%{q}%"),
                        UserField.is_mandatory.ilike(f"%{q}%"),
                    )
                )

            total_records = query.count()

            # 🔹 Determine pagination
            if page is None or limit is None:
                page = 1
                limit = total_records if total_records > 0 else 1  # avoid limit=0
                user_fields = query.all()
            else:
                if page < 1: page = 1
                if limit < 1: limit = 10
                user_fields = query.offset((page - 1) * limit).limit(limit).all()

            result = user_field_serializers.dump(user_fields)

            # 🔹 Structured response
            response = {
                "page": page,
                "page_size": limit,
                "total_records": total_records,
                "total_pages": (total_records + limit - 1) // limit,
                "data": result
            }

            return response, 200

        except IntegrityError as ie:
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            logger.exception("Error fetching user fields")
            return {"error": "Internal error occurred"}, 500

    # ✅ POST - create a new user field
    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided."}, 400

            # Create UserField entry
            UserField.tenant_session = tenant_session
            user_field = UserField(**json_data)
            tenant_session.add(user_field)
            tenant_session.flush()  # To get the new ID

            # Add this field to all users of that user_type
            user_type_id = json_data.get("user_type")
            users = tenant_session.query(User).filter_by(user_type_id=user_type_id, is_active=True).all()

            for user in users:
                user_extra_fields = tenant_session.query(UserExtraFields).filter_by(user_id=user.id).first()

                if user_extra_fields:
                    current_data = user_extra_fields.fields_data or {}
                    current_data[json_data.get('field_name')] = None
                    user_extra_fields.fields_data = current_data
                else:
                    UserExtraFields.tenant_session = tenant_session
                    new_extra_field = UserExtraFields(
                        user_id=user.id,
                        fields_data={json_data.get('field_name'): None}
                    )
                    tenant_session.add(new_extra_field)

            tenant_session.commit()
            return user_field_serializer.dump(user_field), 201

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error creating user field")
            return {"error": "Internal server error"}, 500

    # ✅ PUT - update user field
    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided."}, 400

            field_id = json_data.get("id")
            if not field_id:
                return {"error": "Field ID is required for update"}, 400

            user_field = tenant_session.query(UserField).get(field_id)
            if not user_field:
                return {"error": "Field not found"}, 404

            user_type_id = json_data.get("user_type")
            users = tenant_session.query(User).filter_by(user_type_id=user_type_id, is_active=True).all()

            # Update extra fields for each user
            for user in users:
                user_extra_fields = tenant_session.query(UserExtraFields).filter_by(user_id=user.id).first()
                if user_extra_fields:
                    fields_data = user_extra_fields.fields_data or {}
                    if user_field.field_name in fields_data:
                        del fields_data[user_field.field_name]
                    user_extra_fields.fields_data = fields_data
                else:
                    UserExtraFields.tenant_session = tenant_session
                    new_extra_field = UserExtraFields(
                        user_id=user.id,
                        fields_data={json_data.get('field_name'): None}
                    )
                    tenant_session.add(new_extra_field)

            # Update editable fields in UserField model
            for key, value in json_data.items():
                if hasattr(user_field, key):
                    setattr(user_field, key, value)

            tenant_session.commit()
            return user_field_serializer.dump(user_field), 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error updating user field")
            return {"error": "Internal server error"}, 500

    # ✅ DELETE - mark user field as deleted
    @with_tenant_session_and_user
    def delete(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided."}, 400

            field_id = json_data.get("id")
            if not field_id:
                return {"error": "Field ID is required for delete"}, 400

            user_field = tenant_session.query(UserField).get(field_id)
            if not user_field:
                return {"error": "Field not found"}, 404

            # Check if any user still references this field
            users = tenant_session.query(User).filter_by(user_type_id=user_field.user_type).all()
            for user in users:
                user_extra_fields = tenant_session.query(UserExtraFields).filter_by(user_id=user.id).first()
                if user_extra_fields and user_extra_fields.fields_data:
                    return {"error": "Cannot delete as this field is linked to user(s)"}, 400

            user_field.is_deleted = True
            user_field.is_active = False

            tenant_session.commit()
            return {"message": "Field deleted successfully"}, 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error deleting user field")
            return {"error": "Internal server error"}, 500
