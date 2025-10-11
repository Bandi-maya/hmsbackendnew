from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from Models.BillingSurgeries import BillingSurgeries
from Models.MedicineStock import MedicineStock
from Models.Billing import Billing
from Models.BillingMedicines import BillingMedicines
from Models.BillingTests import BillingTests
from Serializers.BillingSerializers import billing_serializers, billing_serializer
from new import with_tenant_session_and_user


class BillingResource(Resource):
    method_decorators = [jwt_required()]

    # ---------------- GET ----------------
    @with_tenant_session_and_user
    def get(self, db_session):
        try:
            return billing_serializers.dump(db_session.query(Billing).all()), 200
        except Exception as e:
            print(e)
            return {"error": "Internal error occurred"}, 500

    # ---------------- POST ----------------
    @with_tenant_session_and_user
    def post(self, db_session):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            medicines = json_data.get("medicines", [])
            tests = json_data.get("tests", [])
            surgeries = json_data.get("surgeries", [])

            if not (medicines or tests or surgeries):
                return {"error": "Medicines, Tests, or Surgeries are required for billing"}, 400

            total_amount = 0
            patient_id = json_data.get("patient_id")

            # Fetch or create billing record
            billing = db_session.query(Billing).filter(
                Billing.patient_id == patient_id,
                Billing.status != "PAID"
            ).first()
            if not billing:
                billing = Billing(
                    patient_id=patient_id,
                    notes=json_data.get('notes'),
                    prescription_id=json_data.get('prescription_id')
                )
                db_session.add(billing)
                db_session.flush()

            # Handle Medicines
            for med in medicines:
                med_id = med.get("medicine_id")
                qty = int(med.get("quantity", 1))
                if not med_id:
                    continue

                stock_record = db_session.query(MedicineStock).filter_by(medicine_id=med_id).first()
                if not stock_record or stock_record.quantity < qty:
                    db_session.rollback()
                    return {"error": f"Not enough stock for medicine ID {med_id}"}, 400

                stock_record.quantity -= qty
                added_medicine = BillingMedicines(
                    billing_id=billing.id,
                    medicine_id=med_id,
                    quantity=qty
                )
                db_session.add(added_medicine)
                db_session.flush()
                total_amount += added_medicine.price

            # Handle Tests
            for test in tests:
                added_test = BillingTests(
                    billing_id=billing.id,
                    test_id=test.get('test_id')
                )
                db_session.add(added_test)
                db_session.flush()
                total_amount += added_test.price

            # Handle Surgeries
            for surgery in surgeries:
                added_surgery = BillingSurgeries(
                    billing_id=billing.id,
                    surgery_id=surgery.get('surgery_id')
                )
                db_session.add(added_surgery)
                db_session.flush()
                total_amount += added_surgery.price

            billing.total_amount = total_amount
            db_session.commit()

            return billing_serializer.dump(billing), 201

        except (ValueError, TypeError) as ve:
            db_session.rollback()
            return {"error": str(ve)}, 400
        except IntegrityError as ie:
            db_session.rollback()
            return {"error": str(ie.orig)}, 400
        except Exception as e:
            db_session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500

    # ---------------- PUT ----------------
    @with_tenant_session_and_user
    def put(self, db_session):
        try:
            json_data = request.get_json(force=True)
            billing_id = json_data.get("id")
            if not billing_id:
                return {"error": "Billing ID required"}, 400

            billing = db_session.query(Billing).get(billing_id)
            if not billing:
                return {"error": "Billing not found"}, 404

            # Update core fields
            for key in ['patient_id', 'doctor_id', 'notes', 'status']:
                if key in json_data and hasattr(billing, key):
                    setattr(billing, key, json_data[key])

            # TODO: add tenant-aware update logic for medicines, tests, surgeries

            db_session.commit()
            return billing_serializer.dump(billing), 200

        except Exception as e:
            db_session.rollback()
            print(f"PUT /billing error: {e}")
            return {"error": "Internal error occurred"}, 500

    # ---------------- DELETE ----------------
    @with_tenant_session_and_user
    def delete(self, db_session):
        billing_id = request.args.get("id")
        if not billing_id:
            return {"error": "Billing ID required"}, 400

        billing = db_session.query(Billing).get(billing_id)
        if not billing:
            return {"error": "Billing not found"}, 404

        db_session.query(BillingMedicines).filter_by(billing_id=billing_id).delete()
        db_session.query(BillingTests).filter_by(billing_id=billing_id).delete()
        db_session.query(BillingSurgeries).filter_by(billing_id=billing_id).delete()
        db_session.delete(billing)
        db_session.commit()
        return {"message": "Billing deleted successfully"}, 200

    # ---------------- PATCH (Payment) ----------------
    @with_tenant_session_and_user
    def patch(self, db_session):
        try:
            json_data = request.get_json(force=True)
            bill_id = json_data.get("id")
            payment_amount = json_data.get("amount")
            payment_method = json_data.get("method")
            transaction_ref = json_data.get("transaction_ref")

            if not bill_id or not payment_amount or not payment_method:
                return {"error": "Missing required fields: id, amount, method"}, 400

            billing = db_session.query(Billing).get(bill_id)
            if not billing:
                return {"error": f"Bill with ID {bill_id} not found"}, 404

            if billing.amount_paid is None:
                billing.amount_paid = 0.0

            applied_amount = billing.record_payment(
                payment_amount=payment_amount,
                payment_method=payment_method,
                transaction_ref=transaction_ref
            )
            db_session.commit()

            remaining_due = billing.total_amount - (billing.amount_paid or 0)
            return {
                "message": "Payment recorded successfully",
                "applied_amount": applied_amount,
                "new_status": billing.status,
                "amount_paid": billing.amount_paid,
                "total_due": remaining_due
            }, 200

        except ValueError as ve:
            db_session.rollback()
            return {"error": str(ve)}, 400
        except Exception as e:
            db_session.rollback()
            print(f"PATCH /billing error: {e}")
            return {"error": "Internal error occurred during payment processing"}, 500
