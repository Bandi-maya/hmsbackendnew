# import json

# from flask import request
# from flask_jwt_extended import jwt_required
# from flask_restful import Resource
# from sqlalchemy import or_, cast, String
# from sqlalchemy.exc import IntegrityError
# import logging

# from sqlalchemy.orm import aliased

# from Models.Orders import Orders
# from Models.PurchaseOrder import PurchaseOrder
# from Models.Medicine import Medicine
# from Models.Users import User
# from Serializers.PurchaseOrderSerializer import (
#     purchase_order_serializer,
#     purchase_order_serializers,
# )
# from new import with_tenant_session_and_user  # ✅ Tenant session decorator
# from utils.logger import log_activity

# logger = logging.getLogger(__name__)


# class PurchaseOrdersResource(Resource):
#     method_decorators = [jwt_required()]

#     # ✅ GET all purchase orders
#     @with_tenant_session_and_user
#     def get(self, tenant_session, **kwargs):
#         try:
#             # 🔹 Pagination params
#             page = request.args.get("page", type=int)

#             limit = request.args.get("limit", type=int)
#             OrderUser = aliased(User)

#             query = tenant_session.query(PurchaseOrder)
#             query = query.join(Orders)
#             query = query.join(OrderUser, Orders.user_id == OrderUser.id)
#             query = query.join(Medicine).filter(~Medicine.is_deleted)
#             q = request.args.get('q')
#             if q:
#                 query = query.filter(
#                     or_(
#                         # PurchaseOrder.order_id.ilike(f"%{q}%"),
#                         Medicine.name.ilike(f"%{q}%"),
#                         Orders.taken_by.ilike(f"%{q}%"),
#                         Orders.taken_by_phone_no.ilike(f"%{q}%"),
#                         OrderUser.name.ilike(f"%{q}%"),
#                         # PurchaseOrder.medicine_id.ilike(f"%{q}%"),
#                         Medicine.name.ilike(f"%{q}%"),
#                         cast(PurchaseOrder.quantity, String).ilike(f"%{q}%"),
#                         cast(PurchaseOrder.received_date, String).ilike(f"%{q}%"),
#                     )
#                 )
#             # 🔹 Base query
#             total_records = query.count()

#             # 🔹 Apply pagination if both page and limit are provided
#             if page is not None and limit is not None:
#                 if page < 1: page = 1
#                 if limit < 1: limit = 10
#                 query = query.offset((page - 1) * limit).limit(limit)
#             else:
#                 page = 1
#                 limit = total_records

#             orders = query.all()
#             result = purchase_order_serializers.dump(orders)

#             # 🔹 Log activity
#             log_activity("GET_PURCHASE_ORDERS", details=json.dumps({
#                 "count": len(result),
#                 "page": page,
#                 "limit": limit
#             }))

#             # 🔹 Structured response
#             return {
#                 "page": page,
#                 "limit": limit,
#                 "total_records": total_records,
#                 "total_pages": (total_records + limit - 1) // limit if limit else 1,
#                 "data": result
#             }, 200

#         except Exception:
#             logger.exception("Error fetching purchase orders")
#             return {"error": "Internal error occurred"}, 500

#     # ✅ POST create a new purchase order
#     @with_tenant_session_and_user
#     def post(self, tenant_session, **kwargs):
#         try:
#             json_data = request.get_json(force=True)
#             if not json_data:
#                 return {"error": "No input data provided"}, 400

#             medicine_id = json_data.get("medicine_id")
#             if not medicine_id:
#                 return {"error": "Medicine ID required"}, 400

#             # Validate foreign key
#             medicine = tenant_session.query(Medicine).get(medicine_id)
#             if not medicine:
#                 return {"error": f"Medicine ID {medicine_id} not found"}, 404

#             PurchaseOrder.tenant_session = tenant_session
#             order = PurchaseOrder(**json_data)
#             tenant_session.add(order)
#             tenant_session.commit()

#             return purchase_order_serializer.dump(order), 201

#         except IntegrityError as ie:
#             tenant_session.rollback()
#             return {"error": f"Database integrity error: {ie.orig}"}, 400
#         except ValueError as ve:
#             tenant_session.rollback()
#             return {"error": str(ve)}, 400
#         except Exception:
#             tenant_session.rollback()
#             logger.exception("Error creating purchase order")
#             return {"error": "Internal error occurred"}, 500

#     # ✅ PUT update an existing purchase order
#     @with_tenant_session_and_user
#     def put(self, tenant_session, **kwargs):
#         try:
#             json_data = request.get_json(force=True)
#             if not json_data:
#                 return {"error": "No input data provided"}, 400

#             order_id = json_data.get("id")
#             if not order_id:
#                 return {"error": "Order ID required"}, 400

#             order = tenant_session.query(PurchaseOrder).get(order_id)
#             if not order:
#                 return {"error": "Order not found"}, 404

#             for key, value in json_data.items():
#                 if hasattr(order, key):
#                     setattr(order, key, value)

#             tenant_session.commit()
#             return purchase_order_serializer.dump(order), 200

#         except IntegrityError as ie:
#             tenant_session.rollback()
#             return {"error": f"Database integrity error: {ie.orig}"}, 400
#         except Exception:
#             tenant_session.rollback()
#             logger.exception("Error updating purchase order")
#             return {"error": "Internal error occurred"}, 500

#     # ✅ DELETE a purchase order
#     @with_tenant_session_and_user
#     def delete(self, tenant_session, **kwargs):
#         try:
#             order_id = request.args.get("id")
#             if not order_id:
#                 return {"error": "Order ID required"}, 400

#             order = tenant_session.query(PurchaseOrder).get(order_id)
#             if not order:
#                 return {"error": "Order not found"}, 404

#             tenant_session.delete(order)
#             tenant_session.commit()

#             return {"message": "Order deleted successfully"}, 200

#         except IntegrityError as ie:
#             tenant_session.rollback()
#             return {"error": f"Database integrity error: {ie.orig}"}, 400
#         except Exception:
#             tenant_session.rollback()
#             logger.exception("Error deleting purchase order")
#             return {"error": "Internal error occurred"}, 500
