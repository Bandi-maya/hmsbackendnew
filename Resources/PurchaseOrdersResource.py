from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from Models.PurchaseOrder import PurchaseOrder
from Models.Medicine import Medicine
from Serializers.PurchaseOrderSerializer import purchase_order_serializer, purchase_order_serializers
from app_utils import db


class PurchaseOrdersResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        try:
            return purchase_order_serializers.dump(PurchaseOrder.query.all()), 200
        except Exception as e:
            print(e)
            return {"error": "Internal error occurred"}, 500

    def post(self):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            medicine_id = json_data.get("medicine_id")
            if not Medicine.query.get(medicine_id):
                return {"error": f"Medicine ID {medicine_id} not found"}, 404

            order = PurchaseOrder(**json_data)
            db.session.add(order)
            db.session.commit()
            return purchase_order_serializer.dump(order), 201

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
        json_data = request.get_json(force=True)
        order_id = json_data.get("id")
        if not order_id:
            return {"error": "Order ID required"}, 400

        order = PurchaseOrder.query.get(order_id)
        if not order:
            return {"error": "Order not found"}, 404

        for key, value in json_data.items():
            if hasattr(order, key):
                setattr(order, key, value)
        db.session.commit()
        return purchase_order_serializer.dump(order), 200

    def delete(self):
        order_id = request.args.get("id")
        if not order_id:
            return {"error": "Order ID required"}, 400

        order = PurchaseOrder.query.get(order_id)
        if not order:
            return {"error": "Order not found"}, 404

        db.session.delete(order)
        db.session.commit()
        return {"message": "Order deleted successfully"}, 200
