from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from Models.SurgeryDoctor import SurgeryDoctor
from Serializers.SurgeryDoctorSerializers import surgery_doctor_serializer, surgery_doctor_serializers
from app_utils import db


class SurgeryDoctorResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        try:
            # Support getting one by id or all
            sd_id = request.args.get('id')
            if sd_id:
                sd = SurgeryDoctor.query.get(sd_id)
                if not sd:
                    return {"error": "SurgeryDoctor record not found"}, 404
                return surgery_doctor_serializer.dump(sd), 200

            records = SurgeryDoctor.query.all()
            return surgery_doctor_serializers.dump(records), 200

        except Exception as e:
            print(e)
            return {"error": "Internal error occurred"}, 500

    def post(self):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            surgery_id = json_data.get('surgery_id')
            doctor_id = json_data.get('doctor_id')
            role = json_data.get('role')

            if not surgery_id or not doctor_id or not role:
                return {"error": "Missing required fields: surgery_id, doctor_id, role"}, 400

            # Optional: check for duplicate assignment
            existing = SurgeryDoctor.query.filter_by(surgery_id=surgery_id, doctor_id=doctor_id, role=role).first()
            if existing:
                return {"error": "This doctor-role is already assigned to the surgery"}, 400

            record = SurgeryDoctor(
                surgery_id=surgery_id,
                doctor_id=doctor_id,
                role=role
            )
            db.session.add(record)
            db.session.commit()

            return surgery_doctor_serializer.dump(record), 201

        except IntegrityError as ie:
            db.session.rollback()
            return {"error": str(ie.orig)}, 400

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500

    def put(self):
        try:
            json_data = request.get_json(force=True)
            sd_id = json_data.get('id')
            if not sd_id:
                return {"error": "SurgeryDoctor ID required"}, 400

            record = SurgeryDoctor.query.get(sd_id)
            if not record:
                return {"error": "SurgeryDoctor record not found"}, 404

            if 'surgery_id' in json_data:
                record.surgery_id = json_data['surgery_id']

            if 'doctor_id' in json_data:
                record.doctor_id = json_data['doctor_id']

            if 'role' in json_data:
                record.role = json_data['role']

            db.session.commit()

            return surgery_doctor_serializer.dump(record), 200

        except IntegrityError as ie:
            db.session.rollback()
            return {"error": str(ie.orig)}, 400

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500

    def delete(self):
        try:
            sd_id = request.args.get('id')
            if not sd_id:
                return {"error": "SurgeryDoctor ID required"}, 400

            record = SurgeryDoctor.query.get(sd_id)
            if not record:
                return {"error": "SurgeryDoctor record not found"}, 404

            db.session.delete(record)
            db.session.commit()

            return {"message": "SurgeryDoctor record deleted successfully"}, 200

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500
