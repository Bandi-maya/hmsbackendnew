from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from Models.SurgeryType import SurgeryType
from Serializers.SurgeryTypeSerializers import surgery_type_serializer, surgery_type_serializers
from app_utils import db


class SurgeryTypeResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        try:
            surgery_type_id = request.args.get('id')
            if surgery_type_id:
                surgery_type = SurgeryType.query.get(surgery_type_id)
                if not surgery_type:
                    return {"error": "Surgery Type not found"}, 404
                return surgery_type_serializer.dump(surgery_type), 200

            surgery_types = SurgeryType.query.all()
            return surgery_type_serializers.dump(surgery_types), 200

        except Exception as e:
            print(e)
            return {"error": "Internal error occurred"}, 500

    def post(self):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            name = json_data.get('name')
            department_id = json_data.get('department_id')
            description = json_data.get('description')

            if not name or not department_id:
                return {"error": "Missing required fields: name, department_id"}, 400

            # Check if surgery type with same name exists in the department
            existing = SurgeryType.query.filter_by(name=name, department_id=department_id).first()
            if existing:
                return {"error": f"Surgery Type '{name}' already exists in this department"}, 400

            surgery_type = SurgeryType(
                name=name,
                department_id=department_id,
                description=description
            )
            db.session.add(surgery_type)
            db.session.commit()

            return surgery_type_serializer.dump(surgery_type), 201

        except IntegrityError as ie:
            db.session.rollback()
            return {"error": str(ie.orig)}, 400

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500

    def put(self):
        try:
            json_data = request.get_json(force=True)
            surgery_type_id = json_data.get('id')
            if not surgery_type_id:
                return {"error": "Surgery Type ID required"}, 400

            surgery_type = SurgeryType.query.get(surgery_type_id)
            if not surgery_type:
                return {"error": "Surgery Type not found"}, 404

            if 'name' in json_data:
                surgery_type.name = json_data['name']

            if 'department_id' in json_data:
                surgery_type.department_id = json_data['department_id']

            if 'description' in json_data:
                surgery_type.description = json_data['description']

            db.session.commit()

            return surgery_type_serializer.dump(surgery_type), 200

        except IntegrityError as ie:
            db.session.rollback()
            return {"error": str(ie.orig)}, 400

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500

    def delete(self):
        try:
            surgery_type_id = request.args.get('id')
            if not surgery_type_id:
                return {"error": "Surgery Type ID required"}, 400

            surgery_type = SurgeryType.query.get(surgery_type_id)
            if not surgery_type:
                return {"error": "Surgery Type not found"}, 404

            db.session.delete(surgery_type)
            db.session.commit()

            return {"message": "Surgery Type deleted successfully"}, 200

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500
