from flask import request
from flask_restful import Resource
from Models.LabReport import LabReport
from Models.LabRequest import LabRequest
from Serializers.LabReportSerializers import lab_report_serializer, lab_report_serializers
from app_utils import db


class LabReportsResource(Resource):
    def get(self):
        return lab_report_serializers.dump(LabReport.query.all()), 200

    def post(self):
        json_data = request.get_json(force=True)
        if not LabRequest.query.get(json_data.get("request_id")):
            return {"error": "LabRequest not found"}, 404

        lab_report = LabReport(**json_data)
        db.session.add(lab_report)
        db.session.commit()
        return lab_report_serializer.dump(lab_report), 201

    def put(self):
        json_data = request.get_json(force=True)
        report_id = json_data.get("id")
        lab_report = LabReport.query.get(report_id)
        if not lab_report:
            return {"error": "LabReport not found"}, 404
        for key, value in json_data.items():
            if hasattr(lab_report, key):
                setattr(lab_report, key, value)
        db.session.commit()
        return lab_report_serializer.dump(lab_report), 200

    def delete(self):
        report_id = request.args.get("id")
        lab_report = LabReport.query.get(report_id)
        if not lab_report:
            return {"error": "LabReport not found"}, 404
        db.session.delete(lab_report)
        db.session.commit()
        return {"message": "LabReport deleted successfully"}, 200
