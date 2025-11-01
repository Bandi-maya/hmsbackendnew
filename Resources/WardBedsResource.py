import json
from datetime import datetime
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy import or_, cast, String
from sqlalchemy.exc import IntegrityError
import logging

from Models.Billing import Billing
from Models.BillingBeds import BillingBeds
from Models.WardBeds import WardBeds
from Models.Users import User
from Models.Wards import Ward
from Serializers.BillingSerializers import billing_serializer
from Serializers.WardBedsSerializers import ward_beds_serializers, ward_beds_serializer
from new import with_tenant_session_and_user
from utils.logger import log_activity

logger = logging.getLogger(__name__)

class WardBedsResource(Resource):
    method_decorators = [jwt_required()]

    # ✅ GET all ward beds
    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            # 🔹 Optional filters
            ward_id = request.args.get("ward_id", type=int)
            bed_number = request.args.get("bed_number")
            status = request.args.get("status")

            query = tenant_session.query(WardBeds)
            query = query.join(Ward)
            query = query.join(User)

            # 🔹 Apply filters
            if ward_id:
                query = query.filter(WardBeds.ward_id == ward_id)

            if bed_number:
                query = query.filter(WardBeds.bed_number.ilike(f"%{bed_number}%"))

            if status:
                query = query.filter(WardBeds.status.ilike(f"%{status}%"))
            
            query = query.filter(WardBeds.patient_id.isnot(None))

            q = request.args.get('q')
            if q:
                query = query.filter(
                    or_(
                        cast(WardBeds.bed_no, String).ilike(f"%{q}%"),
                        User.name.ilike(f"%{q}%"),
                        # WardBeds.patient_id.ilike(f"%{q}%"),
                        Ward.name.ilike(f"%{q}%"),
                    )
                )

            status = request.args.get('status')
            if status:
                query = query.filter(WardBeds.status == status)

            ward_id = request.args.get('ward_id')
            if ward_id:
                query = query.filter(WardBeds.ward_id == ward_id)

            total_records = query.count()

            # 🔹 Pagination params (optional)
            page = request.args.get("page", type=int) or 1
            limit = request.args.get("limit", type=int) or total_records if total_records > 0 else 1

            if page < 1:
                page = 1
            if limit < 1:
                limit = 10

            # 🔹 Apply pagination
            ward_beds = query.offset((page - 1) * limit).limit(limit).all()
            result = ward_beds_serializers.dump(ward_beds)

            # 🔹 Log activity
            log_activity(
                "GET_WARDS_BEDS",
                details=json.dumps({
                    "count": len(result),
                    "page": page,
                    "limit": limit
                })
            )

            # 🔹 Structured response
            response = {
                "page": page,
                "page_size": limit,
                "total_records": total_records,
                "total_pages": (total_records + limit - 1) // limit,
                "data": result
            }

            return response, 200

        except Exception:
            logger.exception("Error fetching ward beds")
            return {"error": "Internal error occurred"}, 500

    # ✅ POST create new ward bed
    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            WardBeds.tenant_session = tenant_session
            ward_bed = WardBeds(**json_data)
            tenant_session.add(ward_bed)
            tenant_session.flush()

            log_activity("CREATE_WARD_BED", details=json.dumps(ward_beds_serializer.dump(ward_bed)))

            tenant_session.commit()
            return ward_beds_serializer.dump(ward_bed), 201

        except ValueError as ve:
            tenant_session.rollback()
            return {"error": str(ve)}, 400
        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error creating ward bed")
            return {"error": "Internal error occurred"}, 500

    # ✅ PUT update ward bed
    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            ward_id = json_data.get("id")
            if not ward_id:
                return {"error": "Ward bed ID is required"}, 400

            ward_bed = tenant_session.query(WardBeds).get(ward_id)
            if not ward_bed:
                return {"error": "Ward bed not found"}, 404

            old_data = ward_beds_serializer.dump(ward_bed)

            # Handle discharge
            if old_data.get("patient_id") and json_data.get("status") == "DISCHARGED":
                patient_id = old_data["patient_id"]
                json_data["patient_id"] = None
                json_data["admission_date"] = None

                price = float(old_data.get("price", 0))
                try:
                    admission_date = datetime.strptime(old_data.get("admission_date"), "%Y-%m-%dT%H:%M:%S")
                    duration_days = max((datetime.utcnow() - admission_date).days, 1)
                    total_price = price * duration_days
                except Exception as date_err:
                    return {"error": f"Invalid admission date: {date_err}"}, 400

                Billing.tenant_session = tenant_session
                billing = Billing(bed_id=ward_id, patient_id=ward_bed.patient_id, total_amount=total_price)
                tenant_session.add(billing)
                tenant_session.flush()

                # BillingBeds.tenant_session = tenant_session
                # billing_bed = BillingBeds(
                #     billing_id=billing.id,
                #     price=total_price,
                #     bed_id=ward_bed.id
                # )
                # tenant_session.add(billing_bed)

            # Update fields
            for key, value in json_data.items():
                if hasattr(ward_bed, key):
                    setattr(ward_bed, key, value)

            tenant_session.commit()

            new_data = ward_beds_serializer.dump(ward_bed)
            log_activity("UPDATE_WARD_BED", details=json.dumps({"before": old_data, "after": new_data}))

            return new_data, 200

        except ValueError as ve:
            tenant_session.rollback()
            return {"error": str(ve)}, 400
        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error updating ward bed")
            return {"error": "Internal error occurred"}, 500

    # ✅ DELETE ward bed
    @with_tenant_session_and_user
    def delete(self, tenant_session, **kwargs):
        try:
            ward_id = request.args.get("id")
            if not ward_id:
                return {"error": "Ward bed ID is required"}, 400

            ward_bed = tenant_session.query(WardBeds).get(ward_id)
            if not ward_bed:
                return {"error": "Ward bed not found"}, 404

            deleted_data = ward_beds_serializer.dump(ward_bed)
            tenant_session.delete(ward_bed)
            tenant_session.commit()

            log_activity("DELETE_WARD_BED", details=json.dumps(deleted_data))

            return {"message": "Ward bed deleted successfully"}, 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error deleting ward bed")
            return {"error": "Internal error occurred"}, 500
