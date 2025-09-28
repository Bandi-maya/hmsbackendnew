from flask import request
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

# from Models.Invoice import Invoice
from Models.MedicineStock import MedicineStock
from Models.Orders import Orders
from Models.PurchaseOrder import PurchaseOrder
from Models.Medicine import Medicine
from Serializers.OrdersSerializer import order_serializers, order_serializer
from app_utils import db


class OrdersResource(Resource):
    def get(self):
        try:
            return order_serializers.dump(Orders.query.all()), 200
        except Exception as e:
            print(e)
            return {"error": "Internal error occurred"}, 500

    def post(self):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            # Extract order-level fields
            user_id = json_data.get("user_id")
            received_date = json_data.get("received_date")
            items_data = json_data.get("items")

            if not user_id or not items_data:
                return {"error": "Missing user_id or items"}, 400

            # Create the main order record
            order = Orders(user_id=user_id, received_date=received_date, taken_by=json_data.get("taken_by"), taken_by_phone_no=json_data.get("taken_by_phone_no"))
            db.session.add(order)
            db.session.flush()  # Get order.id before committing
            total_amount = 0

            # Create purchase order items
            for item in items_data:
                medicine_id = item.get("medicine_id")
                quantity = item.get("quantity")
                order_date = item.get("order_date")

                medicine = Medicine.query.get(medicine_id)

                medicine_stock = MedicineStock.query.filter_by(medicine_id=medicine_id).first()

                total_amount += medicine_stock.quantity * medicine_stock.price

                if not medicine:
                    db.session.rollback()
                    return {"error": f"Medicine ID {medicine_id} not found"}, 404

                print("jo")

                purchase_item = PurchaseOrder(
                    order_id=order.id,
                    medicine_id=medicine_id,
                    quantity=quantity,
                    order_date=order_date
                )
                db.session.add(purchase_item)

            # invoice = Invoice(order_id=order.id, total_amount=total_amount, created_by=json_data.get("created_by"))
            # print(invoice)
            # db.session.add(invoice)

            db.session.commit()
            return order_serializer.dump(order), 201

        except ValueError as ve:
            db.session.rollback()
            return {"error": str(ve)}, 400
        except IntegrityError as ie:
            db.session.rollback()
            return {"error": str(ie.orig)}, 400
        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500

    def put(self):
        try:
            json_data = request.get_json(force=True)
            order_id = json_data.get("id")
            if not order_id:
                return {"error": "Order ID required"}, 400

            order = Orders.query.get(order_id)
            if not order:
                return {"error": "Order not found"}, 404

            # Update order fields
            order.user_id = json_data.get("user_id", order.user_id)
            order.received_date = json_data.get("received_date", order.received_date)
            order.taken_by = json_data.get("taken_by", order.taken_by)
            order.taken_by_phone_no = json_data.get("received_date", order.taken_by_phone_no)

            items_data = json_data.get("items", [])

            # Clear old items
            PurchaseOrder.query.filter_by(order_id=order.id).delete()

            # Add new items
            for item in items_data:
                medicine_id = item.get("medicine_id")
                quantity = item.get("quantity")
                order_date = item.get("order_date")

                if not Medicine.query.get(medicine_id):
                    db.session.rollback()
                    return {"error": f"Medicine ID {medicine_id} not found"}, 404

                new_item = PurchaseOrder(
                    order_id=order.id,
                    medicine_id=medicine_id,
                    quantity=quantity,
                    order_date=order_date
                )
                db.session.add(new_item)

            db.session.commit()
            return order_serializer.dump(order), 200

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500

    def delete(self):
        try:
            order_id = request.args.get("id")
            if not order_id:
                return {"error": "Order ID required"}, 400

            order = Orders.query.get(order_id)
            if not order:
                return {"error": "Order not found"}, 404

            PurchaseOrder.query.filter_by(order_id=order.id).delete()

            db.session.delete(order)
            db.session.commit()
            return {"message": "Order and its items deleted successfully"}, 200

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500
