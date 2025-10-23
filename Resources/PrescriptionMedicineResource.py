import json
from decimal import Decimal

from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
import logging

from Models.PrescriptionMedicines import PrescriptionMedicines
from Serializers.PrescriptionSerializers import prescription_medicine_serializer, prescription_medicine_serializers
from new import with_tenant_session_and_user
from utils.logger import log_activity

logger = logging.getLogger(__name__)


class PrescriptionMedicinesResource(Resource):
    method_decorators = [jwt_required()]

    # ✅ GET all orders
    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            # 🔹 Pagination params
            page = request.args.get("page", type=int)
            limit = request.args.get("limit", type=int)

            # 🔹 Base query
            query = tenant_session.query(PrescriptionMedicines)
            q = request.args.get('q')
            if q:
                query = query.filter(
                    or_(
                        PrescriptionMedicines.received_date.ilike(f"%{q}%"),
                        PrescriptionMedicines.order_id.ilike(f"%{q}%"),
                        PrescriptionMedicines.taken_by.ilike(f"%{q}%"),
                        PrescriptionMedicines.taken_by_phone_no.ilike(f"%{q}%"),
                    )
                )
            total_records = query.count()

            # 🔹 Apply pagination if both page and limit are provided
            if page is not None and limit is not None:
                if page < 1:
                    page = 1
                if limit < 1:
                    limit = 10
                query = query.offset((page - 1) * limit).limit(limit)
            else:
                # Default to return all records if pagination not provided
                page = 1
                limit = total_records

            orders = query.all()
            result = prescription_medicine_serializers.dump(orders)

            # 🔹 Log activity
            log_activity("GET_PREsCRIPTION_MEDICINES", details=json.dumps({
                "count": len(result),
                "page": page,
                "limit": limit
            }))

            # 🔹 Structured response
            return {
                "page": page,
                "limit": limit,
                "total_records": total_records,
                "total_pages": (total_records + limit - 1) // limit if limit else 1,
                "data": result
            }, 200

        except Exception as e:
            logger.exception("Error fetching prescription medicines")
            return {"error": "Internal error occurred"}, 500

    # ✅ POST create new prescriptionMedicine with items
    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            user_id = json_data.get("patient_id")
            taken_by = json_data.get("taken_by")
            taken_by_phone_no = json_data.get("taken_by_phone_no")
            quantity = json_data.get("quantity")
            items_data = json_data.get("items", [])

            if not user_id or not items_data:
                return {"error": "Missing user_id or items"}, 400

            # ✅ Create the main prescriptionMedicine
            PrescriptionMedicines.tenant_session = tenant_session
            prescriptionMedicine = PrescriptionMedicines(
                patient_id=user_id,
                taken_by=taken_by,
                qunatity=taken_by,
                taken_by_phone_no=taken_by_phone_no
            )
            tenant_session.add(prescriptionMedicine)
            tenant_session.commit()
            return prescription_medicine_serializer.dump(prescriptionMedicine), 201

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error creating prescription Medicine")
            return {"error": "Internal error occurred"}, 500

    # ✅ PUT update existing prescriptionMedicine
    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            order_id = json_data.get("id")
            if not order_id:
                return {"error": "Order ID required"}, 400

            prescriptionMedicine = tenant_session.query(PrescriptionMedicines).get(order_id)
            if not prescriptionMedicine:
                return {"error": "Order not found"}, 404

            # Update basic fields
            prescriptionMedicine.user_id = json_data.get("patient_id", prescriptionMedicine.user_id)
            prescriptionMedicine.taken_by = json_data.get("taken_by", prescriptionMedicine.taken_by)
            prescriptionMedicine.taken_by_phone_no = json_data.get("taken_by_phone_no", prescriptionMedicine.taken_by_phone_no)
            prescriptionMedicine.quantity = json_data.get("quantity", prescriptionMedicine.quantity)

            tenant_session.commit()
            return prescription_medicine_serializer.dump(prescriptionMedicine), 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error updating prescription Medicine")
            return {"error": "Internal error occurred"}, 500

    # ✅ DELETE prescriptionMedicine (and its items)
    @with_tenant_session_and_user
    def delete(self, tenant_session, **kwargs):
        try:
            order_id = request.args.get("id")
            if not order_id:
                return {"error": "Order ID required"}, 400

            prescriptionMedicine = tenant_session.query(PrescriptionMedicines).get(order_id)
            if not prescriptionMedicine:
                return {"error": "Order not found"}, 404

            return {"message": "Order and its items deleted successfully"}, 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error deleting prescription Medicine")
            return {"error": "Internal error occurred"}, 500
