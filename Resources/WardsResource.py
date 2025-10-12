import json
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
import logging

from Models.WardBeds import WardBeds
from Models.Wards import Ward
from Serializers.WardSerializer import ward_serializer, ward_serializers
from new import with_tenant_session_and_user
from utils.logger import log_activity

logger = logging.getLogger(__name__)

class WardsResource(Resource):
    method_decorators = [jwt_required()]

    # ✅ GET all wards
    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            wards = tenant_session.query(Ward).all()
            result = ward_serializers.dump(wards)
            log_activity("GET_WARDS", details=json.dumps({"count": len(result)}))
            return result, 200
        except Exception:
            logger.exception("Error fetching wards")
            return {"error": "Internal error occurred"}, 500

    # ✅ POST create new ward with beds
    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            Ward.tenant_session = tenant_session
            ward = Ward(**json_data)
            tenant_session.add(ward)
            tenant_session.flush()  # to get ward.id

            # Create beds
            for bed_no in range(1, ward.capacity + 1):
                WardBeds.tenant_session = tenant_session
                ward_bed = WardBeds(ward_id=ward.id, bed_no=bed_no)
                tenant_session.add(ward_bed)

            log_activity("CREATE_WARD", details=json.dumps(ward_serializer.dump(ward)))

            tenant_session.commit()
            return ward_serializer.dump(ward), 201

        except ValueError as ve:
            tenant_session.rollback()
            return {"error": str(ve)}, 400
        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error creating ward")
            return {"error": "Internal error occurred"}, 500

    # ✅ PUT update ward and adjust beds
    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            ward_id = json_data.get("id")
            if not ward_id:
                return {"error": "Ward ID is required"}, 400

            ward = tenant_session.query(Ward).get(ward_id)
            if not ward:
                return {"error": "Ward not found"}, 404

            old_data = ward_serializer.dump(ward)
            ward_beds_count = tenant_session.query(WardBeds).filter_by(ward_id=ward_id).count()

            # Add new beds if capacity increased
            if ward_beds_count < json_data.get("capacity", ward.capacity):
                for bed_no in range(ward_beds_count + 1, json_data["capacity"] + 1):
                    tenant_session.add(WardBeds(ward_id=ward.id, bed_no=bed_no))

            # Remove extra beds if capacity reduced
            elif ward_beds_count > json_data.get("capacity", ward.capacity):
                occupied_beds = tenant_session.query(WardBeds).filter(
                    WardBeds.ward_id == ward_id,
                    WardBeds.patient_id.isnot(None)
                ).count()

                if occupied_beds > json_data["capacity"]:
                    raise ValueError("Ward has more occupied beds than its new capacity")

                extra_beds_to_delete = ward_beds_count - json_data["capacity"]
                unoccupied_beds = tenant_session.query(WardBeds).filter(
                    WardBeds.ward_id == ward_id,
                    WardBeds.patient_id.is_(None)
                ).order_by(WardBeds.bed_no.desc()).limit(extra_beds_to_delete).all()

                for bed in unoccupied_beds:
                    tenant_session.delete(bed)

            # Update ward fields
            for key, value in json_data.items():
                if hasattr(ward, key):
                    setattr(ward, key, value)

            tenant_session.commit()

            new_data = ward_serializer.dump(ward)
            log_activity("UPDATE_WARD", details=json.dumps({"before": old_data, "after": new_data}))

            return new_data, 200

        except ValueError as ve:
            tenant_session.rollback()
            return {"error": str(ve)}, 400
        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error updating ward")
            return {"error": "Internal error occurred"}, 500

    # ✅ DELETE ward (soft delete with bed check)
    @with_tenant_session_and_user
    def delete(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            ward_id = json_data.get("id")
            if not ward_id:
                return {"error": "Ward ID is required"}, 400

            ward = tenant_session.query(Ward).get(ward_id)
            if not ward:
                return {"error": "Ward not found"}, 404

            ward_beds_count = tenant_session.query(WardBeds).filter(
                WardBeds.ward_id == ward_id,
                WardBeds.status.notin_(["DISCHARGED"])
            ).count()
            if ward_beds_count != 0:
                return {"error": "Patient is assigned to a bed in the ward."}, 400

            # Soft delete beds
            tenant_session.query(WardBeds).filter(WardBeds.ward_id == ward_id).update(
                {"is_active": False, "is_delete": True}, synchronize_session=False
            )

            # Soft delete ward
            ward.is_active = False
            ward.is_deleted = True

            deleted_data = ward_serializer.dump(ward)
            tenant_session.commit()

            log_activity("DELETE_WARD", details=json.dumps(deleted_data))

            return {"message": "Ward deleted successfully"}, 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error deleting ward")
            return {"error": "Internal error occurred"}, 500
