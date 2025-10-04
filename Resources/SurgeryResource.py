from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from Models.Surgery import Surgery
from Serializers.SurgerySerializers import surgery_serializer, surgery_serializers
from app_utils import db


class SurgeryResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        try:
            surgery_id = request.args.get('id')
            if surgery_id:
                surgery = Surgery.query.get(surgery_id)
                if not surgery:
                    return {"error": "Surgery not found"}, 404
                return surgery_serializer.dump(surgery), 200

            surgeries = Surgery.query.all()
            return surgery_serializers.dump(surgeries), 200

        except Exception as e:
            print(e)
            return {"error": "Internal error occurred"}, 500

    def post(self):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            # Required fields
            patient_id = json_data.get('patient_id')
            surgery_type_id = json_data.get('surgery_type_id')
            scheduled_start_time = json_data.get('scheduled_start_time')

            if not patient_id or not surgery_type_id or not scheduled_start_time:
                return {"error": "Missing required fields: patient_id, surgery_type_id, scheduled_start_time"}, 400

            # Parse datetime
            try:
                scheduled_start_dt = datetime.fromisoformat(scheduled_start_time)
            except Exception:
                return {"error": "Invalid format for scheduled_start_time. Use ISO format."}, 400

            scheduled_end_time = json_data.get('scheduled_end_time')
            scheduled_end_dt = None
            if scheduled_end_time:
                try:
                    scheduled_end_dt = datetime.fromisoformat(scheduled_end_time)
                except Exception:
                    return {"error": "Invalid format for scheduled_end_time. Use ISO format."}, 400

            surgery = Surgery(
                patient_id=patient_id,
                surgery_type_id=surgery_type_id,
                operation_theatre_id=json_data.get('operation_theatre_id'),
                scheduled_start_time=scheduled_start_dt,
                scheduled_end_time=scheduled_end_dt,
                actual_start_time=None,
                actual_end_time=None,
                status=json_data.get('status', 'Scheduled'),
                notes=json_data.get('notes')
            )

            db.session.add(surgery)
            db.session.commit()

            return surgery_serializer.dump(surgery), 201

        except IntegrityError as ie:
            db.session.rollback()
            return {"error": str(ie.orig)}, 400

        except ValueError as ve:
            db.session.rollback()
            return {"error": str(ve)}, 400

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500

    def put(self):
        try:
            json_data = request.get_json(force=True)
            surgery_id = json_data.get('id')
            if not surgery_id:
                return {"error": "Surgery ID required"}, 400

            surgery = Surgery.query.get(surgery_id)
            if not surgery:
                return {"error": "Surgery not found"}, 404

            # Update fields if provided
            if 'patient_id' in json_data:
                surgery.patient_id = json_data['patient_id']

            if 'surgery_type_id' in json_data:
                surgery.surgery_type_id = json_data['surgery_type_id']

            if 'operation_theatre_id' in json_data:
                surgery.operation_theatre_id = json_data['operation_theatre_id']

            if 'scheduled_start_time' in json_data:
                try:
                    surgery.scheduled_start_time = datetime.fromisoformat(json_data['scheduled_start_time'])
                except Exception:
                    return {"error": "Invalid format for scheduled_start_time. Use ISO format."}, 400

            if 'scheduled_end_time' in json_data:
                try:
                    surgery.scheduled_end_time = datetime.fromisoformat(json_data['scheduled_end_time'])
                except Exception:
                    return {"error": "Invalid format for scheduled_end_time. Use ISO format."}, 400

            if 'actual_start_time' in json_data:
                try:
                    surgery.actual_start_time = datetime.fromisoformat(json_data['actual_start_time'])
                except Exception:
                    return {"error": "Invalid format for actual_start_time. Use ISO format."}, 400

            if 'actual_end_time' in json_data:
                try:
                    surgery.actual_end_time = datetime.fromisoformat(json_data['actual_end_time'])
                except Exception:
                    return {"error": "Invalid format for actual_end_time. Use ISO format."}, 400

            if 'status' in json_data:
                surgery.status = json_data['status']

            if 'notes' in json_data:
                surgery.notes = json_data['notes']

            db.session.commit()

            return surgery_serializer.dump(surgery), 200

        except IntegrityError as ie:
            db.session.rollback()
            return {"error": str(ie.orig)}, 400

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500

    def delete(self):
        try:
            surgery_id = request.args.get('id')
            if not surgery_id:
                return {"error": "Surgery ID required"}, 400

            surgery = Surgery.query.get(surgery_id)
            if not surgery:
                return {"error": "Surgery not found"}, 404

            db.session.delete(surgery)
            db.session.commit()

            return {"message": "Surgery deleted successfully"}, 200

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500
