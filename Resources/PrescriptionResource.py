import json
import logging

from flask import request, g
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy import or_, cast, String
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import aliased

from Models.Prescriptions import Prescriptions
from Models.PrescriptionMedicines import PrescriptionMedicines
from Models.PrescriptionTests import PrescriptionTests
from Models.PrescritionSurgeries import PrescriptionSurgeries
from Models.Surgery import Surgery
from Models.Users import User
from Serializers.PrescriptionSerializers import prescription_serializer, prescription_serializers
from new import with_tenant_session_and_user
from utils.logger import log_activity

logger = logging.getLogger(__name__)


class PrescriptionResource(Resource):
    method_decorators = [jwt_required()]

    # ---------------- GET ----------------
    @with_tenant_session_and_user
    def get(self, tenant_session):
        try:
            # 🔹 Pagination params
            page = request.args.get("page", type=int)
            limit = request.args.get("limit", type=int)

            # 🔹 Base query
            query = tenant_session.query(Prescriptions)
            # query = query.join(User).filter(~User.is_deleted)
            Doctor = aliased(User)
            Patient = aliased(User)
            query = query.join(Doctor, Prescriptions.doctor_id == Doctor.id).filter(~Doctor.is_deleted)
            # query = query.join(Patient, Prescriptions.patient_id == Patient.id).filter(~Patient.is_deleted)

            # query = query.join(User, Prescriptions.doctor_id == User.id).filter(~User.is_deleted)
            # query = query.join(User, Prescriptions.patient_id == User.id).filter(~User.is_deleted)
            q = request.args.get('q')
            if q:
                query = query.filter(
                    or_(
                        Doctor.name.ilike(f"%{q}%"),
                        Patient.name.ilike(f"%{q}%"),
                        # cast(Prescriptions.is_billed, String).ilike(f"%{q}%"),
                        Prescriptions.notes.ilike(f"%{q}%"),
                    )
                )
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

            prescriptions = query.all()
            result = prescription_serializers.dump(prescriptions)

            # 🔹 Log activity
            log_activity("GET_PRESCRIPTIONS", details=json.dumps({
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
            logger.exception("Error fetching prescriptions")
            return {"error": "Internal error occurred"}, 500

    # ---------------- POST ----------------
    @with_tenant_session_and_user
    def post(self, tenant_session):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            if not any(json_data.get(k) for k in ("medicines", "tests", "surgeries")):
                return {"error": "Medicines or Tests or Surgeries are required"}, 400

            doctor_id = getattr(g, "user", {}).get("id")
            if not doctor_id:
                return {"error": "Doctor context missing"}, 400

            # Check for existing unbilled prescription
            prescription = tenant_session.query(Prescriptions).filter_by(
                patient_id=json_data.get("patient_id"),
                doctor_id=doctor_id,
                is_billed=False
            ).first()

            if not prescription:
                Prescriptions.tenant_session = tenant_session
                prescription = Prescriptions(
                    patient_id=json_data.get("patient_id"),
                    doctor_id=doctor_id,
                    notes=json_data.get("notes")
                )
                tenant_session.add(prescription)
                tenant_session.flush()

            # Medicines
            for med in json_data.get("medicines", []):
                med_id = med.get("medicine_id")
                if not med_id:
                    continue
                qty = int(med.get("quantity", 1))
                pm = tenant_session.query(PrescriptionMedicines).filter_by(
                    prescription_id=prescription.id,
                    medicine_id=med_id
                ).first()
                if pm:
                    pm.quantity = qty
                else:
                    PrescriptionMedicines.tenant_session = tenant_session
                    tenant_session.add(PrescriptionMedicines(
                        prescription_id=prescription.id,
                        medicine_id=med_id,
                        quantity=qty
                    ))

            # Surgeries
            for surg in json_data.get("surgeries", []):
                surg_type_id = surg.get("surgery_id")
                price = surg.get("price")
                if not surg_type_id:
                    continue
                surgery_rec = tenant_session.query(Surgery).filter_by(
                    surgery_type_id=surg_type_id,
                    patient_id=json_data.get("patient_id")
                ).first()
                if not surgery_rec:
                    Surgery.tenant_session = tenant_session
                    surgery_rec = Surgery(
                        surgery_type_id=surg_type_id,
                        patient_id=json_data.get("patient_id"),
                        price=price
                    )
                    tenant_session.add(surgery_rec)
                    tenant_session.flush()

                if not tenant_session.query(PrescriptionSurgeries).filter_by(
                    prescription_id=prescription.id,
                    surgery_id=surgery_rec.id
                ).first():
                    PrescriptionSurgeries.tenant_session = tenant_session
                    tenant_session.add(PrescriptionSurgeries(
                        prescription_id=prescription.id,
                        surgery_id=surgery_rec.id
                    ))

            # Tests
            for test in json_data.get("tests", []):
                test_id = test.get("test_id")
                if not test_id:
                    continue
                if not tenant_session.query(PrescriptionTests).filter_by(
                    prescription_id=prescription.id,
                    test_id=test_id
                ).first():
                    PrescriptionTests.tenant_session = tenant_session
                    tenant_session.add(PrescriptionTests(
                        prescription_id=prescription.id,
                        test_id=test_id
                    ))

            tenant_session.commit()
            return prescription_serializer.dump(prescription), 201

        except (ValueError, TypeError) as ve:
            tenant_session.rollback()
            return {"error": str(ve)}, 400
        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": str(ie.orig)}, 400
        except Exception as e:
            tenant_session.rollback()
            print("POST /prescriptions error:", e)
            return {"error": "Internal error occurred"}, 500

    # ---------------- PUT ----------------
    @with_tenant_session_and_user
    def put(self, tenant_session):
        try:
            json_data = request.get_json(force=True)
            presc_id = json_data.get("id")
            if not presc_id:
                return {"error": "Prescription ID required"}, 400

            prescription = tenant_session.query(Prescriptions).get(presc_id)
            if not prescription:
                return {"error": "Prescription not found"}, 404

            # Update core fields
            for field in ("patient_id", "doctor_id", "notes"):
                if field in json_data:
                    setattr(prescription, field, json_data.get(field))

            # TODO: update medicines, surgeries, and tests logic if needed

            tenant_session.commit()
            return prescription_serializer.dump(prescription), 200

        except Exception as e:
            tenant_session.rollback()
            print("PUT /prescriptions error:", e)
            return {"error": "Internal error occurred"}, 500

    # ---------------- DELETE ----------------
    @with_tenant_session_and_user
    def delete(self, tenant_session):
        try:
            json_data = request.get_json(force=True)
            presc_id = json_data.get("id")
            if not presc_id:
                return {"error": "Prescription ID required"}, 400

            prescription = tenant_session.query(Prescriptions).get(presc_id)
            if not prescription:
                return {"error": "Prescription not found"}, 404

            tenant_session.query(PrescriptionMedicines).filter_by(prescription_id=presc_id).delete()
            tenant_session.query(PrescriptionTests).filter_by(prescription_id=presc_id).delete()
            tenant_session.query(PrescriptionSurgeries).filter_by(prescription_id=presc_id).delete()
            tenant_session.delete(prescription)
            tenant_session.commit()
            return {"message": "Prescription deleted successfully"}, 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": str(ie.orig)}, 400
        except Exception as e:
            tenant_session.rollback()
            print("DELETE /prescriptions error:", e)
            return {"error": "Internal error occurred"}, 500
