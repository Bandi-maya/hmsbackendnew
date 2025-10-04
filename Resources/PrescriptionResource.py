import json
from flask import request, g
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

# from Models.MedicineStock import MedicineStock
from Models.PrescritionSurgeries import PrescriptionSurgeries
from Models.Surgery import Surgery
from Serializers.SurgerySerializers import surgery_serializer
from Models.Prescriptions import Prescriptions
from Models.PrescriptionMedicines import PrescriptionMedicines
from Models.PrescriptionTests import PrescriptionTests
from Serializers.PrescriptionSerializers import (
    prescription_serializer,
    prescription_serializers,
)
from app_utils import db


class PrescriptionResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        try:
            prescriptions = Prescriptions.query.all()
            return prescription_serializers.dump(prescriptions), 200
        except Exception as e:
            print("GET /prescriptions error:", e)
            return {"error": "Internal error occurred"}, 500

    def post(self):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            medicines = json_data.get("medicines")
            tests = json_data.get("tests")
            surgeries = json_data.get("surgeries")
            has_meds = isinstance(medicines, list) and len(medicines) > 0
            has_tests = isinstance(tests, list) and len(tests) > 0
            has_surgeries = isinstance(surgeries, list) and len(surgeries) > 0

            if not (has_meds or has_tests or has_surgeries):
                return {"error": "Medicines or Tests or Surgeries are required"}, 400

            # Get the doctor id from current user
            doctor_id = None
            if hasattr(g, "user"):
                doctor_id = g.user.get('id')
            if doctor_id is None:
                return {"error": "Doctor context missing"}, 400

            # Try to find existing unbilled prescription
            existing = Prescriptions.query.filter_by(
                patient_id=json_data.get("patient_id"),
                doctor_id=doctor_id,
                is_billed=False
            ).first()

            if existing:
                prescription = prescription_serializer.dump(existing)
            else:
                prescription = Prescriptions(
                    patient_id=json_data.get("patient_id"),
                    doctor_id=doctor_id,
                    notes=json_data.get("notes")
                )
                db.session.add(prescription)
                db.session.flush()
                prescription = prescription_serializer.dump(prescription)

            # Add / update medicines
            for med in (medicines or []):
                med_id = med.get("medicine_id")
                qty = med.get("quantity", 1)
                if med_id is None:
                    continue

                # Convert qty to int early to avoid type issues
                try:
                    qty = int(qty)
                except (ValueError, TypeError):
                    return {"error": "Invalid quantity"}, 400

                pm = PrescriptionMedicines.query.filter_by(
                    prescription_id=prescription.get('id'),
                    medicine_id=med_id
                ).first()

                # medicine_store = MedicineStock.query.filter_by(medicine_id=med_id).first()

                if pm:
                    # if pm.quantity != qty:
                    #     if pm.quantity < qty:
                    #         if medicine_store and medicine_store.quantity >= qty:
                    #             medicine_store.quantity -= (qty-pm.quantity)
                    #         else:
                    #             return {"error": "Not enough medicine quantity"}, 400
                    #     else:
                    #         medicine_store.quantity += (pm.quantity-qty)
                    pm.quantity = qty
                else:
                    new_pm = PrescriptionMedicines(
                        prescription_id=prescription.get('id'),
                        medicine_id=med_id,
                        quantity=qty
                    )
                    db.session.add(new_pm)
                    # if medicine_store and medicine_store.quantity >= qty:
                    #     medicine_store.quantity -= qty
                    # else:
                    #     return {"error": "Not enough medicine quantity"}, 400

            # Add surgeries
            for surg in (surgeries or []):
                surg_type_id = surg.get("surgery_id")
                price = surg.get("price")
                if surg_type_id is None:
                    continue

                # Try to find existing surgery record for this patient & type
                existing_surg = Surgery.query.filter_by(
                    surgery_type_id=surg_type_id,
                    patient_id=json_data.get("patient_id")
                ).first()

                if existing_surg:
                    surg_rec = existing_surg
                else:
                    surg_rec = Surgery(
                        surgery_type_id=surg_type_id,
                        patient_id=json_data.get("patient_id"),
                        price=price
                    )
                    db.session.add(surg_rec)
                    db.session.flush()

                ps = PrescriptionSurgeries.query.filter_by(
                    prescription_id=prescription.get('id'),
                    surgery_id=surg_rec.id
                ).first()
                if not ps:
                    new_ps = PrescriptionSurgeries(
                        prescription_id=prescription.get('id'),
                        surgery_id=surg_rec.id
                    )
                    db.session.add(new_ps)
            print("hi")

            # Add tests
            for t in (tests or []):
                test_id = t.get("test_id")
                if test_id is None:
                    continue
                pt = PrescriptionTests.query.filter_by(
                    prescription_id=prescription.get('id'),
                    test_id=test_id
                ).first()
                if not pt:
                    new_pt = PrescriptionTests(
                        prescription_id=prescription.get('id'),
                        test_id=test_id
                    )
                    db.session.add(new_pt)

            print("hi")
            db.session.commit()
            print("commited")

            # Return the newly created / existing prescription data
            return prescription, 201

        except ValueError as ve:
            db.session.rollback()
            return {"error": str(ve)}, 400
        except IntegrityError as ie:
            db.session.rollback()
            print("GET /prescriptions error:", ie)
            return {"error": str(ie.orig)}, 400
        except Exception as e:
            db.session.rollback()

            print("POST /prescriptions error:", e)
            return {"error": "Internal error occurred"}, 500

    def put(self):
        try:
            json_data = request.get_json(force=True)
            presc_id = json_data.get("id")
            if not presc_id:
                return {"error": "Prescription ID required"}, 400

            prescription = Prescriptions.query.get(presc_id)
            if not prescription:
                return {"error": "Prescription not found"}, 404

            medicines = json_data.get("medicines") or []
            tests = json_data.get("tests") or []
            surgeries = json_data.get("surgeries") or []

            has_meds = isinstance(medicines, list) and len(medicines) > 0
            has_tests = isinstance(tests, list) and len(tests) > 0
            has_surgeries = isinstance(surgeries, list) and len(surgeries) > 0

            if not (has_meds or has_tests or has_surgeries):
                return {"error": "Medicines or Tests or Surgeries are required"}, 400

            # Update core fields
            for key in ("patient_id", "doctor_id", "notes"):
                if key in json_data and hasattr(prescription, key):
                    setattr(prescription, key, json_data.get(key))

            # Medicines update logic
            existing_meds = PrescriptionMedicines.query.filter_by(
                prescription_id=prescription.id
            ).all()
            existing_med_ids = {pm.id for pm in existing_meds}

            new_med_ids = set()
            for med in medicines:
                med_id = med.get("id")
                med_type_id = med.get("medicine_id")
                qty = med.get("quantity", 1)

                # Convert qty to int
                try:
                    qty = int(qty)
                except (ValueError, TypeError):
                    return {"error": "Invalid quantity"}, 400

                if med_id:  # existing record
                    new_med_ids.add(med_id)
                    pm = PrescriptionMedicines.query.get(med_id)
                    if pm.quantity != qty:
                        # Adjust stock based on difference
                        # diff = qty - pm.quantity
                        # medicine_store = MedicineStock.query.filter_by(medicine_id=pm.medicine_id).first()
                        # if diff > 0:
                        #     if medicine_store and medicine_store.quantity >= diff:
                        #         medicine_store.quantity -= diff
                        #     else:
                        #         return {"error": "Not enough medicine quantity"}, 400
                        # elif diff < 0:
                        #     if medicine_store:
                        #         medicine_store.quantity += (-diff)
                        pm.quantity = qty
                else:
                    if med_type_id is not None:
                        # medicine_store = MedicineStock.query.filter_by(medicine_id=med_type_id).first()
                        # if medicine_store and medicine_store.quantity >= qty:
                        #     medicine_store.quantity -= qty
                        # else:
                        #     return {"error": "Not enough medicine quantity"}, 400

                        new_pm = PrescriptionMedicines(
                            prescription_id=prescription.id,
                            medicine_id=med_type_id,
                            quantity=qty
                        )
                        db.session.add(new_pm)

            # Delete removed medicines
            to_delete_meds = existing_med_ids - new_med_ids
            if to_delete_meds:
                # Restore stock for deleted medicines
                meds_to_delete = PrescriptionMedicines.query.filter(
                    PrescriptionMedicines.id.in_(to_delete_meds)
                ).all()
                # for pm in meds_to_delete:
                    # medicine_store = MedicineStock.query.filter_by(medicine_id=pm.medicine_id).first()
                    # if medicine_store:
                    #     medicine_store.quantity += pm.quantity

                PrescriptionMedicines.query.filter(
                    PrescriptionMedicines.id.in_(to_delete_meds)
                ).delete(synchronize_session=False)

            # Surgeries update logic
            existing_surgs = PrescriptionSurgeries.query.filter_by(
                prescription_id=prescription.id
            ).all()
            existing_surg_ids = {ps.id for ps in existing_surgs}

            new_surg_ids = set()
            for surg in surgeries:
                ps_id = surg.get("id")
                surg_type_id = surg.get("surgery_id")
                price = surg.get("price")

                new_s = Surgery.query.filter_by(
                    surgery_type_id=int(surg_type_id),
                    patient_id=json_data.get("patient_id")
                ).first()

                if new_s:
                    new_s.price = price

                if ps_id:
                    new_surg_ids.add(ps_id)
                else:
                    if surg_type_id is None:
                        continue
                    if not new_s:
                        new_s = Surgery(
                            surgery_type_id=surg_type_id,
                            patient_id=prescription.patient_id,
                            price=price
                        )
                        db.session.add(new_s)
                        db.session.flush()
                    new_ps = PrescriptionSurgeries(
                        prescription_id=prescription.id,
                        surgery_id=new_s.id
                    )
                    db.session.add(new_ps)

            to_delete_surgs = existing_surg_ids - new_surg_ids
            if to_delete_surgs:
                PrescriptionSurgeries.query.filter(
                    PrescriptionSurgeries.id.in_(to_delete_surgs)
                ).delete(synchronize_session=False)

            # Tests update logic
            existing_tests = PrescriptionTests.query.filter_by(
                prescription_id=prescription.id
            ).all()
            existing_test_ids = {pt.id for pt in existing_tests}

            new_test_ids = set()
            for t in tests:
                pt_id = t.get("id")
                test_type_id = t.get("test_id")
                if pt_id:
                    new_test_ids.add(pt_id)
                else:
                    if test_type_id is None:
                        continue
                    new_pt = PrescriptionTests(
                        prescription_id=prescription.id,
                        test_id=test_type_id
                    )
                    db.session.add(new_pt)

            to_delete_tests = existing_test_ids - new_test_ids
            if to_delete_tests:
                PrescriptionTests.query.filter(
                    PrescriptionTests.id.in_(to_delete_tests)
                ).delete(synchronize_session=False)

            db.session.commit()
            return prescription_serializer.dump(prescription), 200

        except ValueError as ve:
            db.session.rollback()
            return {"error": str(ve)}, 400
        except IntegrityError as ie:
            db.session.rollback()
            return {"error": str(ie.orig)}, 400
        except Exception as e:
            db.session.rollback()
            print("PUT /prescriptions error:", e)
            return {"error": "Internal error occurred"}, 500

    def delete(self):
        try:
            json_data = request.get_json(force=True)
            presc_id = json_data.get("id")
            if not presc_id:
                return {"error": "Prescription ID required"}, 400

            prescription = Prescriptions.query.get(presc_id)
            if not prescription:
                return {"error": "Prescription not found"}, 404

            # Delete all related entries
            PrescriptionMedicines.query.filter_by(prescription_id=presc_id).delete(synchronize_session=False)
            PrescriptionTests.query.filter_by(prescription_id=presc_id).delete(synchronize_session=False)
            PrescriptionSurgeries.query.filter_by(prescription_id=presc_id).delete(synchronize_session=False)

            db.session.delete(prescription)
            db.session.commit()

            return {"message": "Prescription deleted successfully"}, 200

        except IntegrityError as ie:
            db.session.rollback()
            return {"error": str(ie.orig)}, 400
        except Exception as e:
            db.session.rollback()
            print("DELETE /prescriptions error:", e)
            return {"error": "Internal error occurred"}, 500

