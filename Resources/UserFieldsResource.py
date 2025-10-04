from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from Models.UserField import UserField
from Models.UserExtraFields import UserExtraFields
from Models.Users import User
from Serializers.UserFieldSerializers import user_field_serializers, user_field_serializer
from app_utils import db


class UserFieldsResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        try:
            return user_field_serializers.dump(UserField.query.filter_by(is_deleted=False).all()), 200

        except IntegrityError as ie:
            return {"error": "Database integrity error: " + str(ie.orig)}, 400
        except Exception as e:
            print(e)
            return {"error": "Internal error occurred"}, 500

    def post(self):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided."}, 400

            # ✅ Create UserField entry
            user_field_data = UserField(**json_data)
            db.session.add(user_field_data)
            db.session.flush()

            # ✅ Add this field for all users of that user_type
            user_type_id = json_data.get("user_type")
            users = User.query.filter_by(user_type_id=user_type_id, is_active=True).all()

            for user in users:
                user_extra_fields_data = UserExtraFields.query.filter_by(user_id=user.id).first()
                if user_extra_fields_data:
                    setattr(user_extra_fields_data, 'fields_data', {**user_extra_fields_data.fields_data, json_data.get('field_name'): None})
                else:
                    extra_field = UserExtraFields(
                        user_id=user.id,
                        # field_id=user_field_data.id,
                        fields_data={json_data.get('field_name'): None}
                    )
                    db.session.add(extra_field)

            db.session.commit()
            return user_field_serializer.dump(user_field_data), 201

        except ValueError as ve:
            db.session.rollback()
            return {"error": str(ve)}, 400
        except IntegrityError as ie:
            db.session.rollback()
            return {"error": "Database integrity error: " + str(ie.orig)}, 400
        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal server error"}, 500

    def put(self):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided."}, 400

            field_id = json_data.get("id")
            if not field_id:
                return {"error": "Field ID is required for update"}, 400

            user_field = UserField.query.get(field_id)
            if not user_field:
                return {"error": "Field not found"}, 404

            user_type_id = json_data.get("user_type")
            users = User.query.filter_by(user_type_id=user_type_id, is_active=True).all()

            print(users)

            for user in users:
                user_extra_fields_data = UserExtraFields.query.filter_by(user_id=user.id).first()
                if user_extra_fields_data:
                    extra_fields_data = user_extra_fields_data.fields_data
                    if user_field.field_name in extra_fields_data:
                        del extra_fields_data[user_field.field_name]
                    setattr(user_extra_fields_data, 'fields_data',
                            {**extra_fields_data})
                else:
                    extra_field = UserExtraFields(
                        user_id=user.id,
                        # field_id=user_field_data.id,
                        fields_data={json_data.get('field_name'): None}
                    )
                    db.session.add(extra_field)

            # ✅ Update all editable fields
            for key, value in json_data.items():
                if hasattr(user_field, key):
                    setattr(user_field, key, value)


            db.session.commit()
            return user_field_serializer.dump(user_field), 200

        except ValueError as ve:
            db.session.rollback()
            return {"error": str(ve)}, 400
        except IntegrityError as ie:
            db.session.rollback()
            return {"error": "Database integrity error: " + str(ie.orig)}, 400
        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal server error"}, 500

    def delete(self):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided."}, 400

            field_id = json_data.get("id")
            if not field_id:
                return {"error": "Field ID is required for delete"}, 400

            user_field = UserField.query.get(field_id)
            if not user_field:
                return {"error": "Field not found"}, 404

            users = User.query.filter_by(user_type_id=user_field.user_type).all()
            for user in users:
                user_extra_fields_data = UserExtraFields.query.filter_by(user_id=user.id).first()
                if user_extra_fields_data and user_extra_fields_data.fields_data:
                    return {"error": "Cannot delete as this field is linked to user(s)"}, 400

            user_field.is_deleted = True
            user_field.is_active = False

            db.session.commit()
            return {"message": "Field deleted successfully"}, 200

        except IntegrityError as ie:
            db.session.rollback()
            return {"error": "Database integrity error: " + str(ie.orig)}, 400
        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal server error"}, 500
