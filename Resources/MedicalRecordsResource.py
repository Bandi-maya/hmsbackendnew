import logging

from flask import request
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from Models.MedicalRecords import MedicalRecords
from Models.Users import User
from Serializers.MedicalRecordsSerializer import medical_records_serializers, medical_records_serializer
from app_utils import db


class MedicalRecordsResource(Resource):
    @staticmethod
    def _error_response(message, code=400):
        logging.error(message)
        return {"error": message}, code

    def get(self):
        try:
            return medical_records_serializers.dump(MedicalRecords.query.all()), 200
        except Exception as e:
            logging.exception(e)
            return self._error_response("Internal error occurred", 500)

    def post(self):
        json_data = request.get_json(force=True)
        if not json_data:
            return self._error_response("No input data provided")
        user_id = json_data.get("user_id")
        if not User.query.get(user_id):
            return self._error_response(f"User ID {user_id} not found", 404)
        try:
            medical_record = MedicalRecords(**json_data)
            db.session.add(medical_record)
            db.session.commit()
            return medical_records_serializer.dump(medical_record), 201
        except ValueError as ve:
            db.session.rollback()
            return self._error_response(str(ve))
        except IntegrityError as ie:
            db.session.rollback()
            return self._error_response(str(ie.orig))
        except Exception as e:
            db.session.rollback()
            logging.exception(e)
            return self._error_response("Internal error occurred", 500)

    def put(self):
        json_data = request.get_json(force=True)
        order_id = json_data.get("id")
        if not order_id:
            return self._error_response("Order ID required")
        medical_record = MedicalRecords.query.get(order_id)
        if not medical_record:
            return self._error_response("Medical Record not found", 404)
        try:
            for key, value in json_data.items():
                if hasattr(medical_record, key):
                    setattr(medical_record, key, value)
            db.session.commit()
            return medical_records_serializer.dump(medical_record), 200
        except Exception as e:
            db.session.rollback()
            logging.exception(e)
            return self._error_response("Internal error occurred", 500)

    def delete(self):
        # Currently not supporting deletion of Medical Records. Uncomment below code to enable later.
        # try:
        #     order_id = request.args.get("id")
        #     if not order_id:
        #         return self._error_response("Medical Record ID required")
        #     order = MedicalRecords.query.get(order_id)
        #     if not order:
        #         return self._error_response("Medical Record not found", 404)
        #     db.session.delete(order)
        #     db.session.commit()
        #     return {"message": "Medical Record deleted successfully"}, 200
        # except Exception as e:
        #     db.session.rollback()
        #     logging.exception(e)
        #     return self._error_response("Internal error occurred", 500)
        return self._error_response("Now we are not supporting deletion of Medical Records", 400)
