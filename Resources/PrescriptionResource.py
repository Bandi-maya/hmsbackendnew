import json
from flask import request, g
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from Models.Prescriptions import Prescriptions
from Models.PrescriptionMedicines import PrescriptionMedicines
from Models.PrescriptionTests import PrescriptionTests
from Models.PrescritionSurgeries import PrescriptionSurgeries
from Models.Surgery import Surgery
from Serializers.PrescriptionSerializers import prescription_serializer, prescription_serializers
from new import with_tenant_session_and_user


class PrescriptionResource(Resource):
    method_decorators = [jwt_required()]

    # ---------------- GET ----------------
    @with_tenant_session_and_user
    def get(self, db_session):
        try:
            prescriptions = db_session.query(Prescriptions).all()
            return prescription_serializers.dump(prescriptions), 200
        except Exception as e:
            print("GET /prescriptions error:", e)
            return {"error": "Internal error occurred"}, 500

    # ---------------- POST ----------------
    @with_tenant_session_and_user
    def post(self, db_session):
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
            prescription = db_session.query(Prescriptions).filter_by(
                patient_id=json_data.get("patient_id"),
                doctor_id=doctor_id,
                is_billed=False
            ).first()

            if not prescription:
                Prescriptions.tenant_session = db_session
                prescription = Prescriptions(
                    patient_id=json_data.get("patient_id"),
                    doctor_id=doctor_id,
                    notes=json_data.get("notes")
                )
                db_session.add(prescription)
                db_session.flush()

            # Medicines
            for med in json_data.get("medicines", []):
                med_id = med.get("medicine_id")
                if not med_id:
                    continue
                qty = int(med.get("quantity", 1))
                pm = db_session.query(PrescriptionMedicines).filter_by(
                    prescription_id=prescription.id,
                    medicine_id=med_id
                ).first()
                if pm:
                    pm.quantity = qty
                else:
                    PrescriptionMedicines.tenant_session = db_session
                    db_session.add(PrescriptionMedicines(
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
                surgery_rec = db_session.query(Surgery).filter_by(
                    surgery_type_id=surg_type_id,
                    patient_id=json_data.get("patient_id")
                ).first()
                if not surgery_rec:
                    Surgery.tenant_session = db_session
                    surgery_rec = Surgery(
                        surgery_type_id=surg_type_id,
                        patient_id=json_data.get("patient_id"),
                        price=price
                    )
                    db_session.add(surgery_rec)
                    db_session.flush()

                if not db_session.query(PrescriptionSurgeries).filter_by(
                    prescription_id=prescription.id,
                    surgery_id=surgery_rec.id
                ).first():
                    PrescriptionSurgeries.tenant_session = db_session
                    db_session.add(PrescriptionSurgeries(
                        prescription_id=prescription.id,
                        surgery_id=surgery_rec.id
                    ))

            # Tests
            for test in json_data.get("tests", []):
                test_id = test.get("test_id")
                if not test_id:
                    continue
                if not db_session.query(PrescriptionTests).filter_by(
                    prescription_id=prescription.id,
                    test_id=test_id
                ).first():
                    PrescriptionTests.tenant_session = db_session
                    db_session.add(PrescriptionTests(
                        prescription_id=prescription.id,
                        test_id=test_id
                    ))

            db_session.commit()
            return prescription_serializer.dump(prescription), 201

        except (ValueError, TypeError) as ve:
            db_session.rollback()
            return {"error": str(ve)}, 400
        except IntegrityError as ie:
            db_session.rollback()
            return {"error": str(ie.orig)}, 400
        except Exception as e:
            db_session.rollback()
            print("POST /prescriptions error:", e)
            return {"error": "Internal error occurred"}, 500

    # ---------------- PUT ----------------
    @with_tenant_session_and_user
    def put(self, db_session):
        try:
            json_data = request.get_json(force=True)
            presc_id = json_data.get("id")
            if not presc_id:
                return {"error": "Prescription ID required"}, 400

            prescription = db_session.query(Prescriptions).get(presc_id)
            if not prescription:
                return {"error": "Prescription not found"}, 404

            # Update core fields
            for field in ("patient_id", "doctor_id", "notes"):
                if field in json_data:
                    setattr(prescription, field, json_data.get(field))

            # TODO: update medicines, surgeries, and tests logic if needed

            db_session.commit()
            return prescription_serializer.dump(prescription), 200

        except Exception as e:
            db_session.rollback()
            print("PUT /prescriptions error:", e)
            return {"error": "Internal error occurred"}, 500

    # ---------------- DELETE ----------------
    @with_tenant_session_and_user
    def delete(self, db_session):
        try:
            json_data = request.get_json(force=True)
            presc_id = json_data.get("id")
            if not presc_id:
                return {"error": "Prescription ID required"}, 400

            prescription = db_session.query(Prescriptions).get(presc_id)
            if not prescription:
                return {"error": "Prescription not found"}, 404

            db_session.query(PrescriptionMedicines).filter_by(prescription_id=presc_id).delete()
            db_session.query(PrescriptionTests).filter_by(prescription_id=presc_id).delete()
            db_session.query(PrescriptionSurgeries).filter_by(prescription_id=presc_id).delete()
            db_session.delete(prescription)
            db_session.commit()
            return {"message": "Prescription deleted successfully"}, 200

        except IntegrityError as ie:
            db_session.rollback()
            return {"error": str(ie.orig)}, 400
        except Exception as e:
            db_session.rollback()
            print("DELETE /prescriptions error:", e)
            return {"error": "Internal error occurred"}, 500
