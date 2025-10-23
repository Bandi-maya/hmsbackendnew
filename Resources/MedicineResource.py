from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
import logging

from Models.Medicine import Medicine
from Serializers.MedicineSerializer import medicine_serializer, medicine_serializers
from new import with_tenant_session_and_user
from utils.logger import log_activity

logger = logging.getLogger(__name__)


class MedicineResource(Resource):
    method_decorators = [jwt_required()]

    # ✅ GET all medicines (non-deleted)
    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            # 🔹 Base query (only non-deleted medicines)
            query = tenant_session.query(Medicine).filter_by(is_deleted=False)
            total_records = query.count()

            # 🔹 Pagination params (optional)
            page = request.args.get("page", type=int)
            limit = request.args.get("limit", type=int)

            q = request.args.get('q')
            if q:
                query = query.filter(
                    or_(
                        Medicine.name.ilike(f"%{q}%"),
                        Medicine.description.ilike(f"%{q}%"),
                        Medicine.manufacturer.ilike(f"%{q}%"),
                    )
                )

            # 🔹 Apply pagination if both page and limit are provided
            if page is not None and limit is not None:
                if page < 1: page = 1
                if limit < 1: limit = 10
                query = query.offset((page - 1) * limit).limit(limit)
            else:
                # Return all if pagination not provided
                page = 1
                limit = total_records

            medicines = query.all()
            result = medicine_serializers.dump(medicines)

            # 🔹 Log activity
            log_activity(
                "GET_MEDICINES",
                details={"count": len(result), "page": page, "limit": limit}
            )

            # 🔹 Structured response
            return {
                "page": page,
                "limit": limit,
                "total_records": total_records,
                "total_pages": (total_records + limit - 1) // limit if limit else 1,
                "data": result
            }, 200

        except Exception as e:
            logger.exception("Error fetching medicines")
            return {"error": "Internal error occurred"}, 500

    # ✅ POST create new medicine
    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            Medicine.tenant_session = tenant_session
            medicine = Medicine(**json_data)
            tenant_session.add(medicine)
            tenant_session.commit()

            return medicine_serializer.dump(medicine), 201

        except ValueError as ve:
            tenant_session.rollback()
            return {"error": str(ve)}, 400
        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error creating medicine")
            return {"error": "Internal error occurred"}, 500

    # ✅ PUT update existing medicine
    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            medicine_id = json_data.get("id")
            if not medicine_id:
                return {"error": "Medicine ID required"}, 400

            medicine = tenant_session.query(Medicine).get(medicine_id)
            if not medicine:
                return {"error": "Medicine not found"}, 404

            # Update editable fields
            for key, value in json_data.items():
                if hasattr(medicine, key):
                    setattr(medicine, key, value)

            tenant_session.commit()
            return medicine_serializer.dump(medicine), 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error updating medicine")
            return {"error": "Internal error occurred"}, 500

    # ✅ DELETE (soft delete)
    @with_tenant_session_and_user
    def delete(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            medicine_id = json_data.get("id")
            if not medicine_id:
                return {"error": "Medicine ID required"}, 400

            medicine = tenant_session.query(Medicine).get(medicine_id)
            if not medicine:
                return {"error": "Medicine not found"}, 404

            # Soft delete
            medicine.is_deleted = True
            medicine.is_active = False

            tenant_session.commit()
            return {"message": "Medicine deleted successfully"}, 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error deleting medicine")
            return {"error": "Internal error occurred"}, 500
