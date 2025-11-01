import json
from flask import request, g
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy import func
import logging

from Models.Users import User
from Models.Appointments import Appointment
from Models.WardBeds import WardBeds
from Models.Payments import Payment
from Models.UserType import UserType
from Models.Emergencies import Emergency
from Models.Wards import Wards
from Models.StaffSchedule import StaffSchedule

from new import with_tenant_session_and_user  # ✅ Tenant session decorator
from utils.logger import log_activity

logger = logging.getLogger(__name__)


class StatsResource(Resource):
    method_decorators = [jwt_required()]

    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            # 🔹 Define user type filters
            patient_type = tenant_session.query(UserType.id).filter(UserType.type.ilike("%patient%")).scalar()
            doctor_type = tenant_session.query(UserType.id).filter(UserType.type.ilike("%doctor%")).scalar()

            # ✅ Total Patients
            total_patients = tenant_session.query(func.count(User.id))\
                .filter(User.user_type_id == patient_type)\
                .scalar() or 0

            # ✅ Today's Appointments
            todays_appointments = tenant_session.query(func.count(Appointment.id))\
                .filter(func.date(Appointment.appointment_date) == func.current_date())\
                .scalar() or 0
            
            todays_emergencies = tenant_session.query(func.count(Emergency.id))\
                .filter(Emergency.status == 'active')\
                .scalar() or 0

            # ✅ Available Doctors
            available_doctors = tenant_session.query(func.count(User.id))\
                .filter(User.user_type_id == doctor_type)\
                .scalar() or 0
                # .filter(User.is_available == True)\

            # ✅ Bed Occupancy
            total_beds = tenant_session.query(func.count(WardBeds.id)).scalar() or 0
            occupied_beds = tenant_session.query(func.count(WardBeds.id))\
                .filter(WardBeds.status == "ACTIVE")\
                .scalar() or 0
            bed_occupancy_rate = f"{(occupied_beds / total_beds * 100) if total_beds else 0:.0f}%"

            # ✅ Emergency Cases (if you have such a table, otherwise set to 0)
            emergency_cases = 0

            # ✅ Monthly Revenue
            monthly_revenue = tenant_session.query(func.sum(Payment.amount))\
                .filter(func.date_trunc('month', Payment.created_at) == func.date_trunc('month', func.current_date()))\
                .scalar() or 0
            schedule = {}
            if g.user.get('id'):
                schedule = tenant_session.query(StaffSchedule).filter_by(staff_id= g.user.get('id')).first()
                if not schedule:
                    schedule = {}
            ward_counts = (
                tenant_session.query(
                    Wards.ward_type,
                    func.count(wb.id).label("total_beds"),  # total beds
                    func.count(case([(wb.patient_id == None, 1)])).label("available_beds")  # free beds
                )
                .join(wb, wb.ward_id == Wards.id, isouter=True)  # join WardBeds, include wards with 0 beds
                .group_by(Wards.ward_type)
                .all()
            )

            # Example output
            ward_counts_json = {
                ward_type: {
                    "total_beds": total,
                    "available_beds": available
                }
                for ward_type, total, available in ward_counts
            }
            # ✅ Build stats list
            stats = [
                {
                    "title": "Total Patients",
                    "value": f"{total_patients:,}",
                    "change": "+12.5%",
                    "changeType": "increase",
                    "icon": "TeamOutlined",
                    "description": "Active registered patients"
                },
                {
                    "title": "Emergency Cases",
                    "value": f"{todays_emergencies:,}",
                    "change": "-8.3%",
                    "changeType": "decrease",
                    "icon": "WarningOutlined",
                    "description": "3 critical, 9 moderate"
                },
                {
                    "title": "Today's Appointments",
                    "value": str(todays_appointments),
                    "change": "+5.2%",
                    "changeType": "increase",
                    "icon": "CalendarOutlined",
                    "description": "12 pending, 46 scheduled"
                },
                {
                    "title": "Available Doctors",
                    "value": str(available_doctors),
                    "change": "-2.1%",
                    "changeType": "decrease",
                    "icon": "CheckCircleOutlined",
                    "description": "3 on leave, 5 in surgery"
                },
                {
                    "title": "Bed Occupancy",
                    "value": bed_occupancy_rate,
                    "change": "+3.8%",
                    "changeType": "increase",
                    "icon": "BankOutlined",
                    "description": f"{occupied_beds} of {total_beds} beds occupied"
                },
                {
                    "title": "Emergency Cases",
                    "value": str(emergency_cases),
                    "change": "-8.3%",
                    "changeType": "decrease",
                    "icon": "WarningOutlined",
                    "description": "3 critical, 9 moderate"
                },
                {
                    "title": "Monthly Revenue",
                    "value": f"${monthly_revenue:,.2f}",
                    "change": "+15.3%",
                    "changeType": "increase",
                    "icon": "DollarOutlined",
                    "description": "Current month earnings"
                },
            ]

            # ✅ Log activity
            log_activity("GET_DASHBOARD_STATS", details=json.dumps({"count": len(stats)}))

            return {"data": {"stats": stats}, "schedule": scehdule, "wards": ward_counts_json}, 200

        except Exception as e:
            logger.exception("Error fetching dashboard stats")
            return {"error": str(e)}, 500
