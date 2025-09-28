from flask import request
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from Models.Medicine import Medicine
from Serializers.MedicineSerializer import medicine_serializer, medicine_serializers
from app_utils import db


class MedicineResource(Resource):
    def get(self):
        try:
            return medicine_serializers.dump(Medicine.query.all()), 200
        except Exception as e:
            print(e)
            return {"error": "Internal error occurred"}, 500

    def post(self):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            medicine = Medicine(**json_data)
            db.session.add(medicine)
            db.session.commit()
            return medicine_serializer.dump(medicine), 201

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
        medicine_id = json_data.get("id")
        if not medicine_id:
            return {"error": "Medicine ID required"}, 400

        medicine = Medicine.query.get(medicine_id)
        if not medicine:
            return {"error": "Medicine not found"}, 404

        for key, value in json_data.items():
            if hasattr(medicine, key):
                setattr(medicine, key, value)
        db.session.commit()
        return medicine_serializer.dump(medicine), 200

    def delete(self):
        json_data = request.get_json(force=True)
        medicine_id = json_data.get("id")
        if not medicine_id:
            return {"error": "Medicine ID required"}, 400

        medicine = Medicine.query.get(medicine_id)
        if not medicine:
            return {"error": "Medicine not found"}, 404

        db.session.delete(medicine)
        db.session.commit()
        return {"message": "Medicine deleted successfully"}, 200
