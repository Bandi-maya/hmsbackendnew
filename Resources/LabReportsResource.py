
import logging

from flask import request
from flask_restful import Resource

from Models.LabReport import LabReport
from Models.LabRequest import LabRequest
from Serializers.LabReportSerializers import lab_report_serializer, lab_report_serializers
from app_utils import db


class LabReportsResource(Resource):
    @staticmethod
    def _error_response(message, code=400):
        logging.error(message)
        return {"error": message}, code

    def get(self):
        try:
            return lab_report_serializers.dump(LabReport.query.all()), 200
        except Exception as e:
            logging.exception(e)
            return self._error_response("Internal error occurred", 500)

    def post(self):
        json_data = request.get_json(force=True)
        if not LabRequest.query.get(json_data.get("request_id")):
            return self._error_response("LabRequest not found", 404)
        try:
            lab_report = LabReport(**json_data)
            db.session.add(lab_report)
            db.session.commit()
            return lab_report_serializer.dump(lab_report), 201
        except Exception as e:
            db.session.rollback()
            logging.exception(e)
            return self._error_response("Internal error occurred", 500)

    def put(self):
        json_data = request.get_json(force=True)
        report_id = json_data.get("id")
        lab_report = LabReport.query.get(report_id)
        if not lab_report:
            return self._error_response("LabReport not found", 404)
        try:
            for key, value in json_data.items():
                if hasattr(lab_report, key):
                    setattr(lab_report, key, value)
            db.session.commit()
            return lab_report_serializer.dump(lab_report), 200
        except Exception as e:
            db.session.rollback()
            logging.exception(e)
            return self._error_response("Internal error occurred", 500)

    def delete(self):
        report_id = request.args.get("id")
        lab_report = LabReport.query.get(report_id)
        if not lab_report:
            return self._error_response("LabReport not found", 404)
        try:
            db.session.delete(lab_report)
            db.session.commit()
            return {"message": "LabReport deleted successfully"}, 200
        except Exception as e:
            db.session.rollback()
            logging.exception(e)
            return self._error_response("Internal error occurred", 500)
