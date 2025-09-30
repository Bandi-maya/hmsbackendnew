
import logging

from flask import request
from flask_restful import Resource

from Models.LabRequest import LabRequest
from Models.LabTest import LabTest
from Models.Users import User
from Serializers.LabRequestSerializers import lab_request_serializer, lab_request_serializers
from app_utils import db


class LabRequestsResource(Resource):
    @staticmethod
    def _error_response(message, code=400):
        logging.error(message)
        return {"error": message}, code

    def get(self):
        try:
            return lab_request_serializers.dump(LabRequest.query.all()), 200
        except Exception as e:
            logging.exception(e)
            return self._error_response("Internal error occurred", 500)

    def post(self):
        json_data = request.get_json(force=True)
        if not User.query.get(json_data.get("patient_id")):
            return self._error_response("Patient not found", 404)
        try:
            if isinstance(json_data.get("test_id"), list):
                test_ids = json_data.get("test_id")
                del json_data["test_id"]
                for test in test_ids:
                    if not LabTest.query.get(test):
                        return self._error_response("LabTest not found", 404)
                    lab_request = LabRequest(**json_data, test_id=test)
                    db.session.add(lab_request)
                db.session.commit()
                return {"status": "success"}, 201
            else:
                if not LabTest.query.get(json_data.get("test_id")):
                    return self._error_response("LabTest not found", 404)
                lab_request = LabRequest(**json_data)
                db.session.add(lab_request)
                db.session.commit()
                return lab_request_serializer.dump(lab_request), 201
        except Exception as e:
            db.session.rollback()
            logging.exception(e)
            return self._error_response("Internal error occurred", 500)

    def put(self):
        json_data = request.get_json(force=True)
        request_id = json_data.get("id")
        lab_request = LabRequest.query.get(request_id)
        if not lab_request:
            return self._error_response("LabRequest not found", 404)
        try:
            for key, value in json_data.items():
                if hasattr(lab_request, key):
                    setattr(lab_request, key, value)
            db.session.commit()
            return lab_request_serializer.dump(lab_request), 200
        except Exception as e:
            db.session.rollback()
            logging.exception(e)
            return self._error_response("Internal error occurred", 500)

    def delete(self):
        request_id = request.args.get("id")
        lab_request = LabRequest.query.get(request_id)
        if not lab_request:
            return self._error_response("LabRequest not found", 404)
        try:
            db.session.delete(lab_request)
            db.session.commit()
            return {"message": "LabRequest deleted successfully"}, 200
        except Exception as e:
            db.session.rollback()
            logging.exception(e)
            return self._error_response("Internal error occurred", 500)
