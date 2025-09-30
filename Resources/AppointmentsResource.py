import datetime
import logging

from flask import request
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from Models.Appointments import Appointment
from Serializers.AppointmentSerializers import appointment_serializers
from app_utils import db


class AppointmentsResource(Resource):
    @staticmethod
    def _error_response(message, code=400):
        logging.error(message)
        return {"error": message}, code

    @staticmethod
    def _parse_date(date_str):
        try:
            return datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            return None

    def get(self):
        doctor_id = request.args.get("doctor_id")
        appointment_date = request.args.get("appointment_date")
        query = Appointment.query
        if doctor_id:
            query = query.filter_by(doctor_id=doctor_id)
        if appointment_date:
            date_obj = self._parse_date(appointment_date)
            if not date_obj:
                return self._error_response("Invalid date format. Use YYYY-MM-DD")
            query = query.filter(Appointment.appointment_date == date_obj)
        try:
            appointments = query.all()
            return appointment_serializers.dump(appointments, many=True), 200
        except Exception as e:
            logging.exception(e)
            return self._error_response("Internal error occurred", 500)

    def post(self):
        json_data = request.get_json(force=True)
        if not json_data:
            return self._error_response("No input data provided")
        try:
            appointment = Appointment(**json_data)
            db.session.add(appointment)
            db.session.commit()
            return appointment_serializers.dump(appointment), 201
        except ValueError as ve:
            db.session.rollback()
            return self._error_response(str(ve))
        except IntegrityError as ie:
            db.session.rollback()
            return self._error_response(f"Database integrity error: {str(ie.orig)}")
        except Exception as e:
            db.session.rollback()
            logging.exception(e)
            return self._error_response("Internal error occurred", 500)

    def put(self):
        json_data = request.get_json(force=True)
        if not json_data:
            return self._error_response("No input data provided")
        appointment_id = json_data.get("id")
        if not appointment_id:
            return self._error_response("Appointment ID is required for update")
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return self._error_response("Appointment not found", 404)
        try:
            for key, value in json_data.items():
                if hasattr(appointment, key):
                    setattr(appointment, key, value)
            db.session.commit()
            return appointment_serializers.dump(appointment), 200
        except ValueError as ve:
            db.session.rollback()
            return self._error_response(str(ve))
        except IntegrityError as ie:
            db.session.rollback()
            return self._error_response(f"Database integrity error: {str(ie.orig)}")
        except Exception as e:
            db.session.rollback()
            logging.exception(e)
            return self._error_response("Internal error occurred", 500)

    def delete(self):
        json_data = request.get_json(force=True)
        if not json_data:
            return self._error_response("No input data provided")
        appointment_id = json_data.get("id")
        if not appointment_id:
            return self._error_response("Appointment ID is required for deletion")
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return self._error_response("Appointment not found", 404)
        try:
            db.session.delete(appointment)
            db.session.commit()
            return {"message": "Appointment deleted successfully"}, 200
        except Exception as e:
            db.session.rollback()
            logging.exception(e)
            return self._error_response("Internal error occurred", 500)