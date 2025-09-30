
import logging

from flask import request
from flask_restful import Resource

from Models.LabTest import LabTest
from Serializers.LabTestSerializers import lab_test_serializer, lab_test_serializers
from app_utils import db


class LabTestsResource(Resource):
    @staticmethod
    def _error_response(message, code=400):
        logging.error(message)
        return {"error": message}, code

    def get(self):
        try:
            return lab_test_serializers.dump(LabTest.query.all()), 200
        except Exception as e:
            logging.exception(e)
            return self._error_response("Internal error occurred", 500)

    def post(self):
        json_data = request.get_json(force=True)
        try:
            lab_test = LabTest(**json_data)
            db.session.add(lab_test)
            db.session.commit()
            return lab_test_serializer.dump(lab_test), 201
        except Exception as e:
            db.session.rollback()
            logging.exception(e)
            return self._error_response(str(e))

    def put(self):
        json_data = request.get_json(force=True)
        test_id = json_data.get("id")
        if not test_id:
            return self._error_response("LabTest ID required")
        lab_test = LabTest.query.get(test_id)
        if not lab_test:
            return self._error_response("LabTest not found", 404)
        try:
            for key, value in json_data.items():
                if hasattr(lab_test, key):
                    setattr(lab_test, key, value)
            db.session.commit()
            return lab_test_serializer.dump(lab_test), 200
        except Exception as e:
            db.session.rollback()
            logging.exception(e)
            return self._error_response("Internal error occurred", 500)

    def delete(self):
        test_id = request.args.get("id")
        lab_test = LabTest.query.get(test_id)
        if not lab_test:
            return self._error_response("LabTest not found", 404)
        try:
            db.session.delete(lab_test)
            db.session.commit()
            return {"message": "LabTest deleted successfully"}, 200
        except Exception as e:
            db.session.rollback()
            logging.exception(e)
            return self._error_response("Internal error occurred", 500)
