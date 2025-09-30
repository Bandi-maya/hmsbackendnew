from flask import request
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from app_utils import db
from Serializers.TokenSerializers import TokenSerializers, TokenSerializerz
from Models.Tokens import Token
import datetime
from Models.Appointments import Appointment
from Serializers.AppointmentSerializers import AppointmentSerializers


class TokenResource(Resource):
    def get(self):
        try:
            department_id = request.args.get("department_id")
            date = request.args.get("date")
            doctor_id = request.args.get("doctor_id")
            
            query = Token.query
            if doctor_id:
                    query = query.filter_by(doctor_id=doctor_id)
            if department_id:
                    query = query.filter_by(doctor_id=department_id)
            if date:
                    # Convert string to date
                try:
                    date_obj = datetime.strptime(date, "%Y-%m-%d")
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

            token = Token(**json_data)
            db.session.add(token)
            db.session.commit()
            print(token)

            return TokenSerializerz.dump(token), 201
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

            token_id = json_data.get("id")
            if not token_id:
                return {"error": "Token ID is required for update"}, 400

            token = Token.query.get(token_id)
            if not token:
                return {"error": "Token not found"}, 404

            for key, value in json_data.items():
                if hasattr(token, key):
                    setattr(token, key, value)

            db.session.commit()
            
            return TokenSerializerz.dump(token), 200
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
            token_id = json_data.get("id")
            if not token_id:
                return {"error": "Token ID is required for deletion"}, 400
            token = Token.query.get(token_id)
            if not token:   
                return {"error": "Token not found"}, 404                    
            db.session.delete(token)
            db.session.commit() 
            return {"message": "Token deleted successfully"}, 200
        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500  
    
    