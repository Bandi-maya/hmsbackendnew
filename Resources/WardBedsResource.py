import json
from datetime import datetime

from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from Models.Billing import Billing
from Models.BillingBeds import BillingBeds
from Models.WardBeds import WardBeds
from Serializers.BillingSerializers import billing_serializer
from Serializers.WardBedsSerializers import ward_beds_serializers, ward_beds_serializer
from app_utils import db
from utils.logger import log_activity


class WardBedsResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        try:
            wards = WardBeds.query.all()
            result = ward_beds_serializers.dump(wards)
            log_activity("GET_WARDS_BEDS", details=json.dumps({"count": len(result)}))
            return result, 200
        except Exception as e:
            print(e)
            return {"error": "Internal error occurred"}, 500

    def post(self):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            ward = WardBeds(**json_data)
            db.session.add(ward)
            db.session.flush()

            log_activity("CREATE_WARD_BED", details=json.dumps(ward_beds_serializer.dump(ward)))

            db.session.commit()
            return ward_beds_serializer.dump(ward), 201

        except ValueError as ve:
            db.session.rollback()
            return {"error": str(ve)}, 400

        except IntegrityError as ie:
            db.session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500

    def put(self):
        try:
            json_data = request.get_json(force=True)
            ward_id = json_data.get("id")
            if not ward_id:
                return {"error": "Ward ID is required"}, 400

            ward = WardBeds.query.get(ward_id)
            if not ward:
                return {"error": "Ward not found"}, 404

            old_data = ward_beds_serializer.dump(ward)

            # Check if patient is being discharged
            if old_data.get("patient_id") and json_data.get("status") == "DISCHARGED":
                patient_id = old_data["patient_id"]
                json_data["patient_id"] = None
                json_data["admission_date"] = None
                admission_date_str = old_data.get("admission_date")
                price = float(old_data.get("price", 0))

                # Parse date safely
                try:
                    admission_date = datetime.strptime(admission_date_str, "%Y-%m-%dT%H:%M:%S")
                    current_date = datetime.utcnow()
                    duration_days = (current_date - admission_date).days or 1  # at least 1 day
                    total_price = price * duration_days
                except Exception as date_err:
                    return {"error": f"Invalid admission date format: {date_err}"}, 400

                # Find or create billing record
                billing = Billing.query.filter_by(patient_id=patient_id).first()
                if not billing:
                    billing = Billing(patient_id=patient_id, total_amount=total_price)
                    db.session.add(billing)
                    db.session.flush()  # to get billing.id
                else:
                    billing.total_amount = total_price

                # Create billing bed entry
                billing_bed = BillingBeds(
                    billing_id=billing.id,
                    price=total_price,
                    bed_id=old_data["id"]
                )
                db.session.add(billing_bed)

            # Update the ward fields
            for key, value in json_data.items():
                if hasattr(ward, key):
                    setattr(ward, key, value)

            db.session.commit()

            new_data = ward_beds_serializer.dump(ward)
            log_activity("UPDATE_WARD_BED", details=json.dumps({
                "before": old_data,
                "after": new_data
            }))

            return new_data, 200

        except ValueError as ve:
            db.session.rollback()
            return {"error": str(ve)}, 400

        except IntegrityError as ie:
            db.session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500

    def delete(self):
        try:
            ward_id = request.args.get("id")
            if not ward_id:
                return {"error": "Ward ID is required"}, 400

            ward = WardBeds.query.get(ward_id)
            if not ward:
                return {"error": "Ward not found"}, 404

            deleted_data = ward_beds_serializer.dump(ward)
            db.session.delete(ward)
            db.session.commit()

            log_activity("DELETE_WARD", details=json.dumps(deleted_data))

            return {"message": "Ward deleted successfully"}, 200

        except IntegrityError as ie:
            db.session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500
