from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from Models.Appointments import Appointment
from Serializers.AppointmentSerializers import AppointmentSerializers, AppointmentSerializerz
from app_utils import db
from datetime import datetime


class AppointmentsResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        try:
            doctor_id = request.args.get("doctor_id")
            appointment_date = request.args.get("date")
            query = Appointment.query
            if doctor_id:
                query = query.filter_by(doctor_id=doctor_id)
            
            if appointment_date:
                # Convert string to date
                try:
                    date_obj = datetime.strptime(appointment_date, "%Y-%m-%d")
                    query = query.filter(Appointment.appointment_date == date_obj)
                except Exception:
                    return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400

            appointments = query.all()

            return AppointmentSerializers.dump(appointments, many=True), 200
        except Exception as e:
            print(e)
            return {"error": "Internal error occurred"}, 500
    
    def post(self):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            appointment = Appointment(**json_data)
            db.session.add(appointment)
            db.session.commit()

            return AppointmentSerializerz.dump(appointment), 201
        except ValueError as ve:
            db.session.rollback()
            return {"error": str(ve)}, 400
        except IntegrityError as ie:
            db.session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400 
        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500
        
    def put(self):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            appointment_id = json_data.get("id")
            if not appointment_id:
                return {"error": "Appointment ID is required for update"}, 400

            appointment = Appointment.query.get(appointment_id)
            if not appointment:
                return {"error": "Appointment not found"}, 404

            for key, value in json_data.items():
                if hasattr(appointment, key):
                    setattr(appointment, key, value)

            db.session.commit()
            return AppointmentSerializerz.dump(appointment), 200
        except ValueError as ve:
            db.session.rollback()
            return {"error": str(ve)}, 400
        except IntegrityError as ie:
            db.session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400 
        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500
        
    def delete(self):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            appointment_id = json_data.get("id")
            if not appointment_id:
                return {"error": "Appointment ID is required for deletion"}, 400

            appointment = Appointment.query.get(appointment_id)
            if not appointment:
                return {"error": "Appointment not found"}, 404

            db.session.delete(appointment)
            db.session.commit()
            return {"message": "Appointment deleted successfully"}, 200
        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500