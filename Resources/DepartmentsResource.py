import json
import logging
from datetime import datetime, timedelta

from flask import request, g
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError

from Models.Department import Department
from Models.Users import User
from Models.UserType import UserType
from Serializers.DepartmentSerializers import department_serializers, department_serializer
from extentions import db
from new import with_tenant_session_and_user
from utils.logger import log_activity

logger = logging.getLogger(__name__)


class DepartmentsResource(Resource):
    # This applies the jwt_required decorator to all methods in this class
    method_decorators = [jwt_required()]

    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            # 🔹 Base query
            query = tenant_session.query(Department).filter_by(is_deleted=False)
            users_query = tenant_session.query(User).filter_by(is_deleted=False).join(UserType)
            patient_users_count = users_query.filter(func.upper(UserType.type) == 'PATIENT').count()
            doctor_users_count = users_query.filter(func.upper(UserType.type) == 'DOCTOR').count()
            total_records = query.count()
            active_records = query.filter_by(is_active=True).count()
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            recently_added_records_count = query.filter(Department.is_deleted == False,Department.created_at >= seven_days_ago).count()

            # 🔹 Pagination params (optional)
            page = request.args.get("page", type=int)
            limit = request.args.get("limit", type=int)

            q = request.args.get('q')
            if q:
                query = query.filter(
                    or_(
                        Department.name.ilike(f"%{q}%"),
                        Department.description.ilike(f"%{q}%"),
                    )
                )

            status = request.args.get('status')
            if status:
                query = query.filter(Department.is_active == (status=="ACTIVE"))
                
            # 🔹 Apply pagination if both page and limit are provided
            if page is not None and limit is not None:
                if page < 1: page = 1
                if limit < 1: limit = 10
                query = query.offset((page - 1) * limit).limit(limit)
            else:
                # Return all if pagination not provided
                page = 1
                limit = total_records

            departments = query.all()
            result = department_serializers.dump(departments)

            # 🔹 Log activity
            log_activity(
                "GET_DEPARTMENTS",
                details={"count": len(result), "page": page, "limit": limit}
            )

            # 🔹 Structured response
            return {
                "page": page,
                "limit": limit,
                "total_records": total_records,
                "active_records": active_records,
                "inactive_records": total_records - active_records,
                "recently_added": recently_added_records_count,
                "patient_users_count": patient_users_count,
                "doctor_users_count": doctor_users_count,
                "total_pages": (total_records + limit - 1) // limit if limit else 1,
                "data": result
            }, 200

        except Exception as e:
            logger.exception("Error fetching departments")
            return {"message": "Internal error occurred"}, 500

    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"message": "No input data provided"}, 400

            Department.tenant_session = tenant_session
            department = Department(**json_data)
            tenant_session.add(department)
            tenant_session.commit()

            log_activity("CREATE_DEPARTMENT", details=json.dumps(department_serializer.dump(department)))
            return department_serializer.dump(department), 201
        except IntegrityError as ie:
            tenant_session.rollback()
            return {"message": f"Database integrity error: {str(ie.orig)}"}, 400
        except Exception as e:
            tenant_session.rollback()
            print(e)
            return {"message": "Internal error occurred"}, 500

    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"message": "No input data provided"}, 400

            department_id = json_data.get("id")
            if not department_id:
                return {"message": "Department ID is required for update"}, 400

            department = tenant_session.query(Department).get(department_id)
            if not department:
                return {"message": "Department not found"}, 404

            for key, value in json_data.items():
                if hasattr(department, key):
                    setattr(department, key, value)

            tenant_session.commit()
            log_activity("UPDATE_DEPARTMENT", details=json.dumps(...))
            return department_serializer.dump(department), 200
        except Exception as e:
            tenant_session.rollback()
            print(e)
            return {"message": "Internal error occurred"}, 500

    # @with_tenant_session_and_user
    # def delete(self, tenant_session, **kwargs):
    #     try:
    #         json_data = request.get_json(force=True)
    #         if not json_data:
    #             return {"message": "No input data provided"}, 400

    #         department_id = json_data.get("id")
    #         if not department_id:
    #             return {"message": "Department ID is required"}, 400

    #         department = tenant_session.query(Department).get(department_id)
    #         if not department:
    #             return {"message": "Department not found"}, 404

    #         # This is a soft delete
    #         department.is_deleted = True
    #         department.is_active = False
    #         tenant_session.commit()
    #         log_activity("DELETE_DEPARTMENT", details=json.dumps(...))
    #         return {"message": "Department deleted successfully"}, 200
    #     except Exception as e:
    #         tenant_session.rollback()
    #         print(e)
    #         return {"message": "Internal error occurred"}, 500