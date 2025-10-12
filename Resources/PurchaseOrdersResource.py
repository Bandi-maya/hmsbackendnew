from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
import logging

from Models.PurchaseOrder import PurchaseOrder
from Models.Medicine import Medicine
from Serializers.PurchaseOrderSerializer import (
    purchase_order_serializer,
    purchase_order_serializers,
)
from new import with_tenant_session_and_user  # ✅ Tenant session decorator

logger = logging.getLogger(__name__)


class PurchaseOrdersResource(Resource):
    method_decorators = [jwt_required()]

    # ✅ GET all purchase orders
    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            orders = tenant_session.query(PurchaseOrder).all()
            return purchase_order_serializers.dump(orders), 200
        except Exception:
            logger.exception("Error fetching purchase orders")
            return {"error": "Internal error occurred"}, 500

    # ✅ POST create a new purchase order
    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            medicine_id = json_data.get("medicine_id")
            if not medicine_id:
                return {"error": "Medicine ID required"}, 400

            # Validate foreign key
            medicine = tenant_session.query(Medicine).get(medicine_id)
            if not medicine:
                return {"error": f"Medicine ID {medicine_id} not found"}, 404

            PurchaseOrder.tenant_session = tenant_session
            order = PurchaseOrder(**json_data)
            tenant_session.add(order)
            tenant_session.commit()

            return purchase_order_serializer.dump(order), 201

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except ValueError as ve:
            tenant_session.rollback()
            return {"error": str(ve)}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error creating purchase order")
            return {"error": "Internal error occurred"}, 500

    # ✅ PUT update an existing purchase order
    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            order_id = json_data.get("id")
            if not order_id:
                return {"error": "Order ID required"}, 400

            order = tenant_session.query(PurchaseOrder).get(order_id)
            if not order:
                return {"error": "Order not found"}, 404

            for key, value in json_data.items():
                if hasattr(order, key):
                    setattr(order, key, value)

            tenant_session.commit()
            return purchase_order_serializer.dump(order), 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error updating purchase order")
            return {"error": "Internal error occurred"}, 500

    # ✅ DELETE a purchase order
    @with_tenant_session_and_user
    def delete(self, tenant_session, **kwargs):
        try:
            order_id = request.args.get("id")
            if not order_id:
                return {"error": "Order ID required"}, 400

            order = tenant_session.query(PurchaseOrder).get(order_id)
            if not order:
                return {"error": "Order not found"}, 404

            tenant_session.delete(order)
            tenant_session.commit()

            return {"message": "Order deleted successfully"}, 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error deleting purchase order")
            return {"error": "Internal error occurred"}, 500
