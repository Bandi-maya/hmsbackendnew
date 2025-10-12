from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
import logging

from Models.MedicineStock import MedicineStock
from Models.Medicine import Medicine
from Serializers.MedicineStockSerializer import (
    medicine_stock_serializer,
    medicine_stock_serializers,
)
from new import with_tenant_session_and_user  # ✅ tenant session decorator
from utils.logger import log_activity

logger = logging.getLogger(__name__)


class MedicineStockResource(Resource):
    method_decorators = [jwt_required()]

    # ✅ GET all medicine stock records
    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            # 🔹 Base query
            query = tenant_session.query(MedicineStock)
            total_records = query.count()

            # 🔹 Pagination params (optional)
            page = request.args.get("page", type=int)
            limit = request.args.get("limit", type=int)

            # 🔹 Apply pagination if both page and limit provided
            if page is not None and limit is not None:
                if page < 1: page = 1
                if limit < 1: limit = 10
                query = query.offset((page - 1) * limit).limit(limit)
            else:
                # Return all if pagination not provided
                page = 1
                limit = total_records

            stocks = query.all()
            result = medicine_stock_serializers.dump(stocks)

            # 🔹 Log activity
            log_activity("GET_MEDICINE_STOCK", details={"count": len(result), "page": page, "limit": limit})

            # 🔹 Structured response
            return {
                "page": page,
                "limit": limit,
                "total_records": total_records,
                "total_pages": (total_records + limit - 1) // limit if limit else 1,
                "data": result
            }, 200

        except Exception as e:
            logger.exception("Error fetching medicine stock")
            return {"error": "Internal error occurred"}, 500

    # ✅ POST create a new medicine stock
    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            medicine_id = json_data.get("medicine_id")
            if not medicine_id:
                return {"error": "Medicine ID required"}, 400

            # ✅ Validate foreign key
            medicine = tenant_session.query(Medicine).get(medicine_id)
            if not medicine:
                return {"error": f"Medicine ID {medicine_id} not found"}, 404

            MedicineStock.tenant_session = tenant_session
            stock = MedicineStock(**json_data)
            tenant_session.add(stock)
            tenant_session.commit()

            return medicine_stock_serializer.dump(stock), 201

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except ValueError as ve:
            tenant_session.rollback()
            return {"error": str(ve)}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error creating medicine stock")
            return {"error": "Internal error occurred"}, 500

    # ✅ PUT update an existing stock record
    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            stock_id = json_data.get("id")
            if not stock_id:
                return {"error": "Stock ID required"}, 400

            stock = tenant_session.query(MedicineStock).get(stock_id)
            if not stock:
                return {"error": "Stock not found"}, 404

            for key, value in json_data.items():
                if hasattr(stock, key):
                    setattr(stock, key, value)

            tenant_session.commit()
            return medicine_stock_serializer.dump(stock), 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error updating medicine stock")
            return {"error": "Internal error occurred"}, 500

    # ✅ DELETE a stock record
    @with_tenant_session_and_user
    def delete(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            stock_id = json_data.get("id")
            if not stock_id:
                return {"error": "Stock ID required"}, 400

            stock = tenant_session.query(MedicineStock).get(stock_id)
            if not stock:
                return {"error": "Stock not found"}, 404

            tenant_session.delete(stock)
            tenant_session.commit()

            return {"message": "Stock deleted successfully"}, 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error deleting medicine stock")
            return {"error": "Internal error occurred"}, 500
