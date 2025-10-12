import json
from decimal import Decimal

from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
import logging

from Models.Medicine import Medicine
from Models.MedicineStock import MedicineStock
from Models.Orders import Orders
from Models.PurchaseOrder import PurchaseOrder
from Serializers.OrdersSerializer import order_serializers, order_serializer
from new import with_tenant_session_and_user
from utils.logger import log_activity

logger = logging.getLogger(__name__)


class OrdersResource(Resource):
    method_decorators = [jwt_required()]

    # ✅ GET all orders
    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            # 🔹 Pagination params
            page = request.args.get("page", type=int)
            limit = request.args.get("limit", type=int)

            # 🔹 Base query
            query = tenant_session.query(Orders)
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
            result = order_serializers.dump(orders)

            # 🔹 Log activity
            log_activity("GET_ORDERS", details=json.dumps({
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
            logger.exception("Error fetching orders")
            return {"error": "Internal error occurred"}, 500

    # ✅ POST create new order with items
    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            user_id = json_data.get("user_id")
            received_date = json_data.get("received_date")
            taken_by = json_data.get("taken_by")
            taken_by_phone_no = json_data.get("taken_by_phone_no")
            items_data = json_data.get("items", [])

            if not user_id or not items_data:
                return {"error": "Missing user_id or items"}, 400

            # ✅ Create the main order
            Orders.tenant_session = tenant_session
            order = Orders(
                user_id=user_id,
                received_date=received_date,
                taken_by=taken_by,
                taken_by_phone_no=taken_by_phone_no
            )
            tenant_session.add(order)
            tenant_session.flush()  # Get order.id before commit

            total_amount = 0

            # ✅ Add each item to PurchaseOrder
            for item in items_data:
                medicine_id = item.get("medicine_id")
                quantity = item.get("quantity")
                order_date = item.get("order_date")

                if not medicine_id or not quantity:
                    tenant_session.rollback()
                    return {"error": "Each item must have medicine_id and quantity"}, 400

                medicine = tenant_session.query(Medicine).get(medicine_id)
                if not medicine:
                    tenant_session.rollback()
                    return {"error": f"Medicine ID {medicine_id} not found"}, 404

                medicine_stock = tenant_session.query(MedicineStock).filter_by(medicine_id=medicine_id).first()
                if not medicine_stock:
                    tenant_session.rollback()
                    return {"error": f"No stock found for Medicine ID {medicine_id}"}, 404

                print(medicine_stock.price, quantity)

                total_amount += (Decimal(medicine_stock.price) if medicine_stock.price else Decimal('0')) * int(quantity)

                PurchaseOrder.tenant_session = tenant_session
                purchase_item = PurchaseOrder(
                    order_id=order.id,
                    medicine_id=medicine_id,
                    quantity=quantity,
                    order_date=order_date
                )
                tenant_session.add(purchase_item)

            tenant_session.commit()
            return order_serializer.dump(order), 201

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error creating order")
            return {"error": "Internal error occurred"}, 500

    # ✅ PUT update existing order
    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            order_id = json_data.get("id")
            if not order_id:
                return {"error": "Order ID required"}, 400

            order = tenant_session.query(Orders).get(order_id)
            if not order:
                return {"error": "Order not found"}, 404

            # Update basic fields
            order.user_id = json_data.get("user_id", order.user_id)
            order.received_date = json_data.get("received_date", order.received_date)
            order.taken_by = json_data.get("taken_by", order.taken_by)
            order.taken_by_phone_no = json_data.get("taken_by_phone_no", order.taken_by_phone_no)

            items_data = json_data.get("items", [])

            # ✅ Clear old items
            tenant_session.query(PurchaseOrder).filter_by(order_id=order.id).delete()

            # ✅ Add updated items
            for item in items_data:
                medicine_id = item.get("medicine_id")
                quantity = item.get("quantity")
                order_date = item.get("order_date")

                if not tenant_session.query(Medicine).get(medicine_id):
                    tenant_session.rollback()
                    return {"error": f"Medicine ID {medicine_id} not found"}, 404

                PurchaseOrder.tenant_session = tenant_session
                new_item = PurchaseOrder(
                    order_id=order.id,
                    medicine_id=medicine_id,
                    quantity=quantity,
                    order_date=order_date
                )
                tenant_session.add(new_item)

            tenant_session.commit()
            return order_serializer.dump(order), 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error updating order")
            return {"error": "Internal error occurred"}, 500

    # ✅ DELETE order (and its items)
    @with_tenant_session_and_user
    def delete(self, tenant_session, **kwargs):
        try:
            order_id = request.args.get("id")
            if not order_id:
                return {"error": "Order ID required"}, 400

            order = tenant_session.query(Orders).get(order_id)
            if not order:
                return {"error": "Order not found"}, 404

            tenant_session.query(PurchaseOrder).filter_by(order_id=order.id).delete()
            tenant_session.delete(order)
            tenant_session.commit()

            return {"message": "Order and its items deleted successfully"}, 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error deleting order")
            return {"error": "Internal error occurred"}, 500
