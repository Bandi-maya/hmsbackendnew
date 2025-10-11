from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import logging

from Models.Appointments import Appointment
from Serializers.AppointmentSerializers import AppointmentSerializers, AppointmentSerializerz
from new import with_tenant_session_and_user

logger = logging.getLogger(__name__)


class AppointmentsResource(Resource):
    method_decorators = [jwt_required()]

    # ✅ GET appointments
    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            doctor_id = request.args.get("doctor_id")
            appointment_date = request.args.get("date")

            query = tenant_session.query(Appointment)

            if doctor_id:
                query = query.filter_by(doctor_id=doctor_id)

            if appointment_date:
                try:
                    date_obj = datetime.strptime(appointment_date, "%Y-%m-%d")
                    query = query.filter(Appointment.appointment_date == date_obj)
                except Exception:
                    return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400

            appointments = query.filter_by(is_deleted=False).all()
            return AppointmentSerializers.dump(appointments, many=True), 200

        except Exception:
            logger.exception("Error fetching appointments")
            return {"error": "Internal error occurred"}, 500

    # ✅ POST create new appointment
    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            appointment = Appointment(**json_data)
            tenant_session.add(appointment)
            tenant_session.commit()

            return AppointmentSerializerz.dump(appointment), 201

        except ValueError as ve:
            tenant_session.rollback()
            return {"error": str(ve)}, 400
        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error creating appointment")
            return {"error": "Internal error occurred"}, 500

    # ✅ PUT update appointment
    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            appointment_id = json_data.get("id")
            if not appointment_id:
                return {"error": "Appointment ID is required for update"}, 400

            appointment = tenant_session.query(Appointment).get(appointment_id)
            if not appointment:
                return {"error": "Appointment not found"}, 404

            for key, value in json_data.items():
                if hasattr(appointment, key):
                    setattr(appointment, key, value)

            tenant_session.commit()
            return AppointmentSerializerz.dump(appointment), 200

        except ValueError as ve:
            tenant_session.rollback()
            return {"error": str(ve)}, 400
        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error updating appointment")
            return {"error": "Internal error occurred"}, 500

    # ✅ DELETE appointment (soft delete)
    @with_tenant_session_and_user
    def delete(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            appointment_id = json_data.get("id")
            if not appointment_id:
                return {"error": "Appointment ID is required for deletion"}, 400

            appointment = tenant_session.query(Appointment).get(appointment_id)
            if not appointment:
                return {"error": "Appointment not found"}, 404

            appointment.is_deleted = True
            appointment.is_active = False

            tenant_session.commit()
            return {"message": "Appointment deleted successfully"}, 200

        except Exception:
            tenant_session.rollback()
            logger.exception("Error deleting appointment")
            return {"error": "Internal error occurred"}, 500
