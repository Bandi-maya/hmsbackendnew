from flask import request
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from Models.MedicineStock import MedicineStock
from Models.Medicine import Medicine
from Serializers.MedicineStockSerializer import medicine_stock_serializer, medicine_stock_serializers
from app_utils import db


class MedicineStockResource(Resource):
    def get(self):
        try:
            return medicine_stock_serializers.dump(MedicineStock.query.all()), 200
        except Exception as e:
            print(e)
            return {"error": "Internal error occurred"}, 500

    def post(self):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            # Validate foreign key
            medicine_id = json_data.get("medicine_id")
            if not Medicine.query.get(medicine_id):
                return {"error": f"Medicine ID {medicine_id} not found"}, 404

            stock = MedicineStock(**json_data)
            db.session.add(stock)
            db.session.commit()
            return medicine_stock_serializer.dump(stock), 201

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
        stock_id = json_data.get("id")
        if not stock_id:
            return {"error": "Stock ID required"}, 400

        stock = MedicineStock.query.get(stock_id)
        if not stock:
            return {"error": "Stock not found"}, 404

        for key, value in json_data.items():
            if hasattr(stock, key):
                setattr(stock, key, value)
        db.session.commit()
        return medicine_stock_serializer.dump(stock), 200

    def delete(self):
        json_data = request.get_json(force=True)
        stock_id = json_data.get("id")
        # stock_id = request.args.get("id")
        if not stock_id:
            return {"error": "Stock ID required"}, 400

        stock = MedicineStock.query.get(stock_id)
        if not stock:
            return {"error": "Stock not found"}, 404

        db.session.delete(stock)
        db.session.commit()
        return {"message": "Stock deleted successfully"}, 200
