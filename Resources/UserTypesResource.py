from flask import request
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
import logging

from Models.UserType import UserType
from Models.Users import User
from Serializers.UserTypeSerializer import user_type_serializers, user_type_serializer
from app_utils import db

logger = logging.getLogger(__name__)

class UserTypesResource(Resource):
    def get(self):
        try:
            user_types = UserType.query.filter_by(is_active=True).all()
            return user_type_serializers.dump(user_types), 200
        except Exception as e:
            logger.exception("Error fetching user types")
            return {"error": "Internal error occurred"}, 500

    def post(self):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            new_user_type = UserType(**json_data)
            db.session.add(new_user_type)
            db.session.commit()

            return user_type_serializer.dump(new_user_type), 201

        except ValueError as ve:
            return {"error": str(ve)}, 400

        except IntegrityError as ie:
            db.session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400

        except Exception as e:
            logger.exception("Error creating user type")
            return {"error": "Internal error occurred"}, 500

    def put(self):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            user_type_id = json_data.get("id")
            if not user_type_id:
                return {"error": "User Type ID is required for update"}, 400

            user_type = UserType.query.get(user_type_id)
            if not user_type:
                return {"error": "User Type not found"}, 404

            # Dynamically update fields
            for key, value in json_data.items():
                if hasattr(user_type, key):
                    setattr(user_type, key, value)

            db.session.commit()
            return user_type_serializer.dump(user_type), 200

        except ValueError as ve:
            return {"error": str(ve)}, 400

        except IntegrityError as ie:
            db.session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400

        except Exception as e:
            logger.exception("Error updating user type")
            return {"error": "Internal error occurred"}, 500

    def delete(self):
        try:
            return {"error": "Now we are not allowing to delete the User Type."}
            json_data = request.get_json(force=True)
            user_type_id = json_data.get("id")
            if not user_type_id:
                return {"error": "User Type ID is required for delete"}, 400

            user_type = UserType.query.get(user_type_id)
            if not user_type:
                return {"error": "User Type not found"}, 404

            user = User.query.filter_by(user_type_id=user_type.id, is_active=True).first()
            if user:
                return {"error": "User Type can not be deleted as a user(s) is assigned to it"}, 404


            user_type.is_active = False
            db.session.commit()

            return {"message": "User type deactivated successfully"}, 200

        except Exception as e:
            logger.exception("Error deleting user type")
            return {"error": "Internal error occurred"}, 500
