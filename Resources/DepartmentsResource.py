import logging

from flask import request
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from Models.Department import Department
from Serializers.DepartmentSerializers import department_serializers, department_serializer
from app_utils import db


class DepartmentsResource(Resource):
    @staticmethod
    def _error_response(message, code=400):
        logging.error(message)
        return {"error": message}, code

    def get(self):
        try:
            return department_serializers.dump(Department.query.all()), 200
        except Exception as e:
            logging.exception(e)
            return self._error_response("Internal error occurred", 500)

    def post(self):
        json_data = request.get_json(force=True)
        if not json_data:
            return self._error_response("No input data provided")
        try:
            department = Department(**json_data)
            db.session.add(department)
            db.session.commit()
            return department_serializer.dump(department), 201
        except ValueError as ve:
            db.session.rollback()
            return self._error_response(str(ve))
        except IntegrityError as ie:
            db.session.rollback()
            return self._error_response(f"Database integrity error: {str(ie.orig)}")
        except Exception as e:
            db.session.rollback()
            logging.exception(e)
            return self._error_response("Internal error occurred", 500)

    def put(self):
        json_data = request.get_json(force=True)
        if not json_data:
            return self._error_response("No input data provided")
        department_id = json_data.get("id")
        if not department_id:
            return self._error_response("Department ID is required for update")
        department = Department.query.get(department_id)
        if not department:
            return self._error_response("Department not found", 404)
        try:
            for key, value in json_data.items():
                if hasattr(department, key):
                    setattr(department, key, value)
            db.session.commit()
            return department_serializer.dump(department), 200
        except ValueError as ve:
            db.session.rollback()
            return self._error_response(str(ve))
        except IntegrityError as ie:
            db.session.rollback()
            return self._error_response(f"Database integrity error: {str(ie.orig)}")
        except Exception as e:
            db.session.rollback()
            logging.exception(e)
            return self._error_response("Internal error occurred", 500)

    def delete(self):
        # Currently not supporting department deletion. Uncomment below code to enable later.
        # try:
        #     department_id = request.args.get("id")
        #     if not department_id:
        #         return self._error_response("Department ID is required")
        #     department = Department.query.get(department_id)
        #     if not department:
        #         return self._error_response("Department not found", 404)
        #     db.session.delete(department)
        #     db.session.commit()
        #     return {"message": "Department deleted successfully"}, 200
        # except IntegrityError as ie:
        #     db.session.rollback()
        #     return self._error_response(f"Database integrity error: {str(ie.orig)}")
        # except Exception as e:
        #     db.session.rollback()
        #     logging.exception(e)
        #     return self._error_response("Internal error occurred", 500)
        return self._error_response("Now we are not allowing to delete the department.")
