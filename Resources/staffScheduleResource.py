import json
import logging
from datetime import datetime

from flask import request, current_app
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.orm import joinedload

from Models.staffSchedule import StaffSchedule, Schedule
from new import with_tenant_session_and_user
from utils.logger import log_activity

logger = logging.getLogger(__name__)


class StaffScheduleResource(Resource):
    method_decorators = [jwt_required()]

    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            staff_id = request.args.get('doctor_id')

            if staff_id:
                schedule = tenant_session.query(StaffSchedule).filter_by(staff_id=staff_id).first()

                if not schedule:
                    return {}, 200

                result = {
                    "doctor_id": schedule.staff_id,
                    "start_time": schedule.start_time.strftime('%H:%M'),
                    "end_time": schedule.end_time.strftime('%H:%M'),
                    "status": schedule.status.name,
                    "schedule_items": [
                        {
                            "title": item.title,
                            "start_time": item.start_time.strftime('%H:%M'),
                            "end_time": item.end_time.strftime('%H:%M'),
                            "location": item.location,
                            "notes": item.notes
                        } for item in schedule.items
                    ]
                }
                log_activity("GET_STAFF_SCHEDULE",
                             details=json.dumps({"staff_id": staff_id}))
                return result, 200
            else:
                schedules = tenant_session.query(StaffSchedule).options(joinedload(StaffSchedule.items)).all()
                results = []
                for schedule in schedules:
                    results.append({
                        "doctor_id": schedule.staff_id,
                        "start_time": schedule.start_time.strftime('%H:%M'),
                        "end_time": schedule.end_time.strftime('%H:%M'),
                        "status": schedule.status.name,
                        "schedule_items": [
                            {
                                "title": item.title,
                                "start_time": item.start_time.strftime('%H:%M'),
                                "end_time": item.end_time.strftime('%H:%M'),
                                "location": item.location,
                                "notes": item.notes
                            } for item in schedule.items
                        ]
                    })
                log_activity("GET_ALL_STAFF_SCHEDULES", details=json.dumps({"count": len(results)}))
                return results, 200

        except Exception as e:
            current_app.logger.error(e)
            return {"error": "Internal Server Error"}, 500

    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            data = request.get_json()

            required_fields = ['doctor_id', 'start_time', 'end_time', 'schedule_items']
            if not all(field in data for field in required_fields):
                return {"error": f"Missing required fields: {', '.join(required_fields)}"}, 400

            try:
                start_time = datetime.strptime(data['start_time'], '%H:%M').time()
                end_time = datetime.strptime(data['end_time'], '%H:%M').time()
            except ValueError as e:
                return {"error": f"Invalid date or time format: {e}"}, 400

            staff_schedule = tenant_session.query(StaffSchedule).filter_by(
                staff_id=data['doctor_id']
            ).first()

            if not staff_schedule:
                staff_schedule = StaffSchedule(
                    staff_id=data["doctor_id"],
                    start_time=start_time,
                    end_time=end_time,
                    status=data.get("status", "scheduled")
                )

                schedule_items = []
                for item_data in data.get("schedule_items", []):
                    try:
                        item_start_time = datetime.strptime(item_data['start_time'], '%H:%M').time()
                        item_end_time = datetime.strptime(item_data['end_time'], '%H:%M').time()
                    except ValueError as e:
                        return {"error": f"Invalid time format in schedule_items: {e}"}, 400
                    except KeyError as e:
                        return {"error": f"Missing key in schedule_items: {e}"}, 400

                    schedule_items.append(Schedule(
                        title=item_data.get("title"),
                        start_time=item_start_time,
                        end_time=item_end_time,
                        location=item_data.get("location"),
                        notes=item_data.get("notes")
                    ))

                staff_schedule.items = schedule_items

                tenant_session.add(staff_schedule)
                tenant_session.commit()

            response_data = {
                "doctor_id": staff_schedule.staff_id,
                "start_time": staff_schedule.start_time.strftime('%H:%M'),
                "end_time": staff_schedule.end_time.strftime('%H:%M'),
                "status": staff_schedule.status.name,
                "schedule_items": [
                    {
                        "title": item.title,
                        "start_time": item.start_time.strftime('%H:%M'),
                        "end_time": item.end_time.strftime('%H:%M'),
                        "location": item.location,
                        "notes": item.notes
                    } for item in staff_schedule.items
                ]
            }

            log_activity("CREATE_STAFF_SCHEDULE", details=json.dumps({"id": staff_schedule.id}))
            return response_data, 201

        except Exception as e:
            tenant_session.rollback()
            current_app.logger.error(e)
            return {"error": f"An internal error occurred: {e}"}, 500
