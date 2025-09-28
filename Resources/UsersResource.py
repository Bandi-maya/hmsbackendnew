# import requests
from flask import request
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from Models.UserExtraFields import UserExtraFields
from Models.UserField import UserField
from Models.Users import User
from Serializers.UserSerializers import user_serializers, user_serializer
from app_utils import db


class UsersResource(Resource):
    def get(self):
        try:
            user_id = request.args.get('user_id', type=int)
            user_type_id = request.args.get('user_type_id')
            department_id = request.args.get('department_id')

            if user_id:
                user = User.query.get(user_id)
                if not user:
                    return {"error": "User not found"}, 404
                return user_serializers.dump(user), 200

            if user_type_id:
                users = User.query.filter_by(user_type_id=user_type_id).all()
                return user_serializers.dump(users, many=True), 200

            if department_id:
                users = User.query.filter_by(department_id=department_id).all()
                return user_serializers.dump(users, many=True), 200

            # If no filters, return all users
            users = User.query.all()
            return user_serializers.dump(users), 200

        except IntegrityError as ie:
            return {"error": "Database integrity error: " + str(ie.orig)}, 400
        except Exception as e:
            print(e)
            return {"error": "Internal error occurred"}, 500

    def post(self):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            extra_fields_data = json_data.pop('extra_fields', {})
            user_type_id = json_data.get('user_type_id')

            if not user_type_id:
                return {"error": "No user_type_id provided"}, 400

            json_data['password'] = "Password124"

            user = User(**json_data)
            db.session.add(user)
            db.session.flush()

            fields = UserField.query.filter_by(user_type=user_type_id).all()

            for field in fields:
                if field.is_mandatory and not extra_fields_data.get(field.field_name):
                    return {"error": f"{field.field_name} is missing in extra fields."}, 400
                elif not extra_fields_data.get(field.field_name):
                    extra_fields_data[field.field_name] = None

            db.session.add(UserExtraFields(
                user_id=user.id,
                fields_data=extra_fields_data
            ))

            db.session.commit()
            return user_serializer.dump(user), 201

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
                return {"error": "No input data provided"}, 400

            user_id = json_data.get("id")
            if not user_id:
                return {"error": "User ID is required for update"}, 400

            user = User.query.get(user_id)
            if not user:
                return {"error": "User not found"}, 404

            for key, value in json_data.items():
                if hasattr(user, key) and key != "extra_fields":
                    setattr(user, key, value)

            extra_fields_data = json_data.pop('extra_fields', {})

            user_type_id = json_data.get('user_type_id')

            if not user_type_id:
                return {"error": "No user_type_id provided"}, 400

            fields = UserField.query.filter_by(user_type=user_type_id).all()

            for field in fields:
                if field.is_mandatory and not extra_fields_data.get(field.field_name):
                    return {"error": f"{field.field_name} is missing in extra fields."}, 400
                elif not extra_fields_data.get(field.field_name):
                    extra_fields_data[field.field_name] = None

            user_extra_fields_data = UserExtraFields.query.filter_by(user_id=user_id).first()
            if user_extra_fields_data:
                setattr(user_extra_fields_data, 'fields_data', {**extra_fields_data})
            else:
                extra_field = UserExtraFields(
                    user_id=user.id,
                    fields_data=extra_fields_data
                )
                db.session.add(extra_field)

            db.session.commit()
            return user_serializer.dump(user), 200

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
                return {"error": "No input data provided"}, 400

            user_id = json_data.get("id")
            if not user_id:
                return {"error": "User ID is required for delete"}, 400

            user = User.query.get(user_id)
            if not user:
                return {"error": "User not found"}, 404

            UserExtraFields.query.filter_by(user_id=user_id).delete()

            db.session.delete(user)
            db.session.commit()

            return {"message": "User and associated fields deleted successfully"}, 200

        except IntegrityError as ie:
            db.session.rollback()
            return {"error": "Database integrity error", "details": str(ie.orig)}, 400
        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal server error", "details": str(e)}, 500