from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from Models.MedicalRecords import MedicalRecords
from Models.Users import User
from Serializers.MedicalRecordsSerializer import medical_records_serializers, medical_records_serializer
from app_utils import db


class MedicalRecordsResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        try:
            return medical_records_serializers.dump(MedicalRecords.query.all()), 200
        except Exception as e:
            print(e)
            return {"error": "Internal error occurred"}, 500

    def post(self):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            user_id = json_data.get("user_id")
            if not User.query.get(user_id):
                return {"error": f"User ID {user_id} not found"}, 404

            medicalRecord = MedicalRecords(**json_data)
            db.session.add(medicalRecord)
            db.session.commit()
            return medical_records_serializer.dump(medicalRecord), 201

        except ValueError as ve:
            db.session.rollback()
            return {"error": str(ve)}, 400
        except IntegrityError as ie:
            db.session.rollback()
            return {"error": str(ie.orig)}, 400
        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500

    def put(self):
        json_data = request.get_json(force=True)
        order_id = json_data.get("id")
        if not order_id:
            return {"error": "Order ID required"}, 400

        medicalRecord = MedicalRecords.query.get(order_id)
        if not medicalRecord:
            return {"error": "Medical Record not found"}, 404

        for key, value in json_data.items():
            if hasattr(medicalRecord, key):
                setattr(medicalRecord, key, value)
        db.session.commit()
        return medical_records_serializer.dump(medicalRecord), 200

    def delete(self):
        return {"error": "Now we are not supporting deletion of Medical Records"}, 400
        order_id = request.args.get("id")
        if not order_id:
            return {"error": "Medical Record ID required"}, 400

        order = MedicalRecords.query.get(order_id)
        if not order:
            return {"error": "Medical Record not found"}, 404

        db.session.delete(order)
        db.session.commit()
        return {"message": "Medical Record deleted successfully"}, 200
