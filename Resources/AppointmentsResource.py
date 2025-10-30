from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy import or_, cast, String
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import logging
from sqlalchemy.orm import aliased

from Models.Appointments import Appointment
from Models.Users import User
from Serializers.AppointmentSerializers import AppointmentSerializers, AppointmentSerializerz
from new import with_tenant_session_and_user

logger = logging.getLogger(__name__)

class AppointmentsResource(Resource):
    method_decorators = [jwt_required()]

    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            doctor_id = request.args.get("doctor_id")
            appointment_date = request.args.get("date")
            status = request.args.get("status")

            query = tenant_session.query(Appointment).filter(Appointment.is_deleted == False)
            Doctor = aliased(User)
            Patient = aliased(User)
            query = query.join(Doctor, Appointment.doctor_id == Doctor.id).filter(Doctor.is_deleted == False)
            query = query.join(Patient, Appointment.patient_id == Patient.id).filter(Patient.is_deleted == False)

            # Filters
            if doctor_id:
                query = query.filter(Appointment.doctor_id == doctor_id)

            if appointment_date:
                try:
                    date_obj = datetime.strptime(appointment_date, "%Y-%m-%d")
                    start = datetime.combine(date_obj, datetime.min.time())
                    end = datetime.combine(date_obj, datetime.max.time())
                    query = query.filter(Appointment.appointment_date.between(start, end))
                except ValueError:
                    return {"error": "Invalid date format. Use YYYY-MM-DD"}, 400
                    
            total_records = query.count()
            scheduled_records = query.filter(Appointment.status == 'SCHEDULED').count()
            completed_records = query.filter(Appointment.status == 'COMPLETED').count()
            canceled_records = query.filter(Appointment.status == 'CANCELED').count()

            if status:
                query = query.filter(Appointment.status == status)

            # Search
            q = request.args.get("q")
            if q:
                query = query.filter(
                    or_(
                        Doctor.name.ilike(f"%{q}%"),
                        Doctor.email.ilike(f"%{q}%"),
                        Patient.name.ilike(f"%{q}%"),
                        Patient.email.ilike(f"%{q}%"),
                        cast(Appointment.appointment_date, String).ilike(f"%{q}%"),
                        cast(Appointment.appointment_start_time, String).ilike(f"%{q}%"),
                        cast(Appointment.appointment_end_time, String).ilike(f"%{q}%"),
                        cast(Appointment.duration, String).ilike(f"%{q}%"),
                    )
                )

            # Pagination
            page = request.args.get("page", default=1, type=int)
            limit = request.args.get("limit", default=20, type=int)
            if page < 1: page = 1
            if limit < 1: limit = 20

            appointments = query.offset((page - 1) * limit).limit(limit).all()

            result = AppointmentSerializers.dump(appointments)

            return {
                "page": page,
                "limit": limit,
                "scheduled_records": scheduled_records,
                "completed_records": completed_records,
                "canceled_records": canceled_records,
                "total_records": total_records,
                "total_pages": (total_records + limit - 1) // limit,
                "data": result
            }, 200

        except Exception:
            logger.exception("Error fetching appointments")
            return {"error": "Internal error occurred"}, 500

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

    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            appointment_id = json_data.get("id")
            if not appointment_id:
                return {"error": "Appointment ID is required for update"}, 400

            appointment = tenant_session.get(Appointment, appointment_id)
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

    @with_tenant_session_and_user
    def delete(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            appointment_id = json_data.get("id")
            if not appointment_id:
                return {"error": "Appointment ID is required for deletion"}, 400

            appointment = tenant_session.get(Appointment, appointment_id)
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
