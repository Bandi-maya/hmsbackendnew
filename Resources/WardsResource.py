import json
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy import or_, cast, String
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

    # GET all wards
    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            ward_name = request.args.get("name")
            department_id = request.args.get("department_id", type=int)
            query = tenant_session.query(Ward)

            if ward_name:
                query = query.filter(Ward.name.ilike(f"%{ward_name}%"))
            if department_id:
                query = query.filter(Ward.department_id == department_id)

            q = request.args.get("q")
            if q:
                query = query.filter(
                    or_(
                        Ward.name.ilike(f"%{q}%"),
                        Ward.ward_type.ilike(f"%{q}%"),
                        cast(Ward.capacity, String).ilike(f"%{q}%"),
                        Ward.email.ilike(f"%{q}%"),
                    )
                )

            total_records = query.count()
            page = request.args.get("page", type=int) or 1
            limit = request.args.get("limit", type=int) or (total_records if total_records > 0 else 1)

            wards = query.offset((page - 1) * limit).limit(limit).all()
            result = ward_serializers.dump(wards)

            log_activity("GET_WARDS", details=json.dumps({"count": len(result), "page": page, "limit": limit}))

            return {
                "page": page,
                "page_size": limit,
                "total_records": total_records,
                "total_pages": (total_records + limit - 1) // limit,
                "data": result
            }, 200

        except Exception:
            logger.exception("Error fetching wards")
            return {"error": "Internal error occurred"}, 500

    # POST create new ward with beds
    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            ward = Ward(**json_data)
            tenant_session.add(ward)
            tenant_session.flush()  # get ward.id

            # Create beds
            WardBeds.tenant_session = tenant_session
            for bed_no in range(1, ward.capacity + 1):
                bed = WardBeds(
                    ward_id=ward.id,
                    bed_no=f"{ward.name}-{bed_no}"
                )
                tenant_session.add(bed)

            tenant_session.commit()
            log_activity("CREATE_WARD", details=json.dumps(ward_serializer.dump(ward)))
            return ward_serializer.dump(ward), 201

        except ValueError as ve:
            print(ve)
            tenant_session.rollback()
            return {"error": str(ve)}, 400
        except IntegrityError as ie:
            print(ie)
            tenant_session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error creating ward")
            return {"error": "Internal error occurred"}, 500

    # PUT update ward and adjust beds
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
            old_name = ward.name  # Save old name for bed renaming

            # Update ward fields
            for key, value in json_data.items():
                if hasattr(ward, key):
                    setattr(ward, key, value)

            # Adjust beds if capacity changed
            WardBeds.tenant_session = tenant_session
            current_bed_count = tenant_session.query(WardBeds).filter_by(ward_id=ward_id).count()
            if ward.capacity > current_bed_count:
                # Add new beds
                for bed_no in range(current_bed_count + 1, ward.capacity + 1):
                    bed = WardBeds(
                        ward_id=ward.id,
                        bed_no=f"{ward.name}-{bed_no}"
                    )
                    tenant_session.add(bed)
            elif ward.capacity < current_bed_count:
                # Remove unoccupied beds if capacity decreased
                unoccupied_beds = tenant_session.query(WardBeds)\
                    .filter(WardBeds.ward_id == ward_id, WardBeds.patient_id.is_(None))\
                    .order_by(WardBeds.bed_no.desc()).all()
                beds_to_remove = current_bed_count - ward.capacity
                if len(unoccupied_beds) < beds_to_remove:
                    raise ValueError("Cannot reduce capacity: not enough unoccupied beds")
                for bed in unoccupied_beds[:beds_to_remove]:
                    tenant_session.delete(bed)

            # Update bed names if ward name changed
            if 'name' in json_data and json_data['name'] != old_name:
                beds = tenant_session.query(WardBeds).filter_by(ward_id=ward_id).order_by(WardBeds.id).all()
                for idx, bed in enumerate(beds, start=1):
                    bed.bed_no = f"{ward.name}-{idx}"

            tenant_session.commit()
            log_activity(
                "UPDATE_WARD",
                details=json.dumps({"before": old_data, "after": ward_serializer.dump(ward)})
            )
            return ward_serializer.dump(ward), 200

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

    # DELETE ward (soft delete)
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

            active_beds_count = tenant_session.query(WardBeds)\
                .filter(WardBeds.ward_id == ward_id, WardBeds.patient_id.isnot(None)).count()
            if active_beds_count > 0:
                return {"error": "Cannot delete ward: patients assigned to beds"}, 400

            # Soft delete beds
            tenant_session.query(WardBeds).filter(WardBeds.ward_id == ward_id).update(
                {"is_active": False, "is_delete": True}, synchronize_session=False
            )

            # Soft delete ward
            ward.is_active = False
            ward.is_deleted = True

            tenant_session.commit()
            log_activity("DELETE_WARD", details=json.dumps(ward_serializer.dump(ward)))
            return {"message": "Ward deleted successfully"}, 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error deleting ward")
            return {"error": "Internal error occurred"}, 500
