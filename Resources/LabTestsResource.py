from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from Models.LabTest import LabTest
from Serializers.LabTestSerializers import lab_test_serializer, lab_test_serializers
from app_utils import db
from sqlalchemy.exc import IntegrityError


class LabTestsResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        try:
            return lab_test_serializers.dump(LabTest.query.all()), 200
        except Exception as e:
            print(e)
            return {"error": "Internal error occurred"}, 500

    def post(self):
        try:
            json_data = request.get_json(force=True)
            lab_test = LabTest(**json_data)
            db.session.add(lab_test)
            db.session.commit()
            return lab_test_serializer.dump(lab_test), 201
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 400

    def put(self):
        json_data = request.get_json(force=True)
        test_id = json_data.get("id")
        if not test_id:
            return {"error": "LabTest ID required"}, 400

        lab_test = LabTest.query.get(test_id)
        if not lab_test:
            return {"error": "LabTest not found"}, 404

        for key, value in json_data.items():
            if hasattr(lab_test, key):
                setattr(lab_test, key, value)
        db.session.commit()
        return lab_test_serializer.dump(lab_test), 200

    def delete(self):
        test_id = request.args.get("id")
        lab_test = LabTest.query.get(test_id)
        if not lab_test:
            return {"error": "LabTest not found"}, 404
        db.session.delete(lab_test)
        db.session.commit()
        return {"message": "LabTest deleted successfully"}, 200
