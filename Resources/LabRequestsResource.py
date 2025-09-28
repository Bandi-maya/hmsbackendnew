from flask import request
from flask_restful import Resource
from Models.LabRequest import LabRequest
from Models.Users import User
from Models.LabTest import LabTest
from Serializers.LabRequestSerializers import lab_request_serializer, lab_request_serializers
from app_utils import db


class LabRequestsResource(Resource):
    def get(self):
        return lab_request_serializers.dump(LabRequest.query.all()), 200

    def post(self):
        json_data = request.get_json(force=True)
        # Validate foreign keys
        if not User.query.get(json_data.get("patient_id")):
            return {"error": "Patient not found"}, 404

        if type(json_data.get("test_id")) is list:
            test_ids = json_data.get("test_id")
            del json_data["test_id"]
            for test in test_ids:
                if not LabTest.query.get(test):
                    return {"error": "LabTest not found"}, 404
                print(test, json_data)
                lab_request = LabRequest(**json_data, test_id=test)
                db.session.add(lab_request)
            db.session.commit()
            return {"status": "success"}, 201
        else:
            if not LabTest.query.get(json_data.get("test_id")):
                return {"error": "LabTest not found"}, 404
            lab_request = LabRequest(**json_data)
            db.session.add(lab_request)
            db.session.commit()
            return lab_request_serializer.dump(lab_request), 201

    def put(self):
        json_data = request.get_json(force=True)
        request_id = json_data.get("id")
        lab_request = LabRequest.query.get(request_id)
        if not lab_request:
            return {"error": "LabRequest not found"}, 404
        for key, value in json_data.items():
            if hasattr(lab_request, key):
                setattr(lab_request, key, value)
        db.session.commit()
        return lab_request_serializer.dump(lab_request), 200

    def delete(self):
        request_id = request.args.get("id")
        lab_request = LabRequest.query.get(request_id)
        if not lab_request:
            return {"error": "LabRequest not found"}, 404
        db.session.delete(lab_request)
        db.session.commit()
        return {"message": "LabRequest deleted successfully"}, 200
