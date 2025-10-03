from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from Models.Department import Department
from Serializers.DepartmentSerializers import department_serializers, department_serializer
from app_utils import db

class DepartmentsResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        try:
            return department_serializers.dump(Department.query.all()), 200
        except Exception as e:
            print(e)
            return {"error": "Internal error occurred"}, 500

    def post(self):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            department = Department(**json_data)
            db.session.add(department)
            db.session.commit()

            return department_serializer.dump(department), 201

        except ValueError as ve:
            db.session.rollback()
            return {"error": str(ve)}, 400

        except IntegrityError as ie:
            db.session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500

    def put(self):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            department_id = json_data.get("id")
            if not department_id:
                return {"error": "Department ID is required for update"}, 400

            department = Department.query.get(department_id)
            if not department:
                return {"error": "Department not found"}, 404

            for key, value in json_data.items():
                if hasattr(department, key):
                    setattr(department, key, value)

            db.session.commit()
            return department_serializer.dump(department), 200

        except ValueError as ve:
            db.session.rollback()
            return {"error": str(ve)}, 400

        except IntegrityError as ie:
            db.session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500

    def delete(self):
        try:
            return {"error": "Now we are not allowing to delete the department."}
            department_id = request.args.get("id")
            if not department_id:
                return {"error": "Department ID is required"}, 400

            department = Department.query.get(department_id)
            if not department:
                return {"error": "Department not found"}, 404

            db.session.delete(department)
            db.session.commit()
            return {"message": "Department deleted successfully"}, 200

        except IntegrityError as ie:
            db.session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500
