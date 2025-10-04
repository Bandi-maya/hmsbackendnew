from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from Models.BillingSurgeries import BillingSurgeries
from Models.MedicineStock import MedicineStock
from app_utils import db
from Serializers.BillingSerializers import billing_serializers, billing_serializer
from Models.Billing import Billing
from Models.BillingMedicines import BillingMedicines
from Models.BillingTests import BillingTests


class BillingResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        try:
            return billing_serializers.dump(Billing.query.all()), 200
        except Exception as e:
            print(e)
            return {"error": "Internal error occurred"}, 500

    def post(self):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            medicines = json_data.get("medicines")
            tests = json_data.get("tests")
            surgeries = json_data.get("surgeries")
            isMedicinesExists = bool(medicines and isinstance(medicines, list))
            isTestsExists = bool(tests and isinstance(tests, list))
            isSurgeriesExists = bool(surgeries and isinstance(surgeries, list))

            if not (isMedicinesExists or isTestsExists or isSurgeriesExists):
                return {"error": "Medicines or Tests or Surgeries are required for a billing"}

            total_amount = 0

            billing = Billing.query.filter(
                Billing.patient_id == json_data.get("patient_id"),
                Billing.status != "PAID"
            ).first()
            if billing:
                total_amount += billing.total_amount
            else:
                billing = Billing(patient_id=json_data.get('patient_id'), notes=json_data.get('notes'),
                                  prescription_id=json_data.get('prescription_id'))
                db.session.add(billing)
                db.session.flush()

            # Handle stock deduction for medicines
            for medicine in medicines or []:
                medicine_id = medicine.get('medicine_id')
                qty = medicine.get('quantity', 1)
                if medicine_id is None:
                    continue

                # Check stock availability
                stock_record = MedicineStock.query.filter_by(medicine_id=medicine_id).first()
                if not stock_record or stock_record.quantity < qty:
                    db.session.rollback()
                    return {"error": f"Not enough stock for medicine ID {medicine_id}"}, 400

                # Deduct stock
                stock_record.quantity -= qty

                added_medicine = BillingMedicines(billing_id=billing.id, medicine_id=medicine_id, quantity=qty)
                db.session.add(added_medicine)
                db.session.flush()
                total_amount += added_medicine.price

            # Add tests
            for test in tests or []:
                added_test = BillingTests(billing_id=billing.id, test_id=test.get('test_id'))
                db.session.add(added_test)
                db.session.flush()
                total_amount += added_test.price

            # Add surgeries
            for surgery in surgeries or []:
                added_surgery = BillingSurgeries(billing_id=billing.id, surgery_id=surgery.get('surgery_id'))
                db.session.add(added_surgery)
                db.session.flush()
                total_amount += added_surgery.price

            billing.total_amount = total_amount
            db.session.commit()
            return billing_serializer.dump(billing), 201

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
        try:
            json_data = request.get_json(force=True)
            order_id = json_data.get("id")
            if not order_id:
                return {"error": "Billing ID required"}, 400

            medicines = json_data.get("medicines") or []
            tests = json_data.get("tests") or []
            surgeries = json_data.get("surgeries") or []

            if not (medicines or tests or surgeries):
                return {"error": "Medicines or Tests or Surgeries are required for a billing"}

            billing = Billing.query.get(order_id)
            if not billing:
                return {"error": "Billing not found"}, 404

            # Update core billing fields
            for key, value in json_data.items():
                if hasattr(billing, key) and key in ['patient_id', 'doctor_id', 'notes', 'status']:
                    setattr(billing, key, value)

            # Handle medicine stock updates:
            existing_meds = BillingMedicines.query.filter_by(billing_id=billing.id).all()
            existing_meds_dict = {med.id: med for med in existing_meds}
            existing_meds_by_med_id = {med.medicine_id: med for med in existing_meds}

            new_med_ids = set()
            total_amount = 0

            for medicine in medicines:
                med_id = medicine.get('id')
                medicine_type_id = medicine.get('medicine_id')
                qty = medicine.get('quantity', 1)

                if med_id:  # Existing record, update quantity and adjust stock accordingly
                    new_med_ids.add(med_id)
                    existing_med = existing_meds_dict.get(med_id)
                    if not existing_med:
                        continue  # Defensive

                    old_qty = existing_med.quantity
                    diff_qty = qty - old_qty  # positive means more quantity needed

                    # Check stock if diff_qty > 0
                    if diff_qty > 0:
                        stock_record = MedicineStock.query.filter_by(medicine_id=medicine_type_id).first()
                        if not stock_record or stock_record.quantity < diff_qty:
                            db.session.rollback()
                            return {"error": f"Not enough stock for medicine ID {medicine_type_id}"}, 400
                        stock_record.quantity -= diff_qty
                    elif diff_qty < 0:
                        # Revert stock because quantity decreased
                        stock_record = MedicineStock.query.filter_by(medicine_id=medicine_type_id).first()
                        if stock_record:
                            stock_record.quantity += (-diff_qty)

                    existing_med.quantity = qty
                    total_amount += existing_med.price * qty

                else:  # New medicine entry
                    if medicine_type_id is None:
                        continue
                    stock_record = MedicineStock.query.filter_by(medicine_id=medicine_type_id).first()
                    if not stock_record or stock_record.quantity < qty:
                        db.session.rollback()
                        return {"error": f"Not enough stock for medicine ID {medicine_type_id}"}, 400
                    stock_record.quantity -= qty

                    new_med = BillingMedicines(billing_id=billing.id, medicine_id=medicine_type_id, quantity=qty)
                    db.session.add(new_med)
                    total_amount += new_med.price * qty

            # Delete removed medicines and revert stock
            for med in existing_meds:
                if med.id not in new_med_ids:
                    stock_record = MedicineStock.query.filter_by(medicine_id=med.medicine_id).first()
                    if stock_record:
                        stock_record.quantity += med.quantity
                    db.session.delete(med)

            # Surgeries update (unchanged)
            existing_surgs = BillingSurgeries.query.filter_by(billing_id=billing.id).all()
            existing_surg_ids = {ps.id for ps in existing_surgs}

            new_surg_ids = set()
            for surgery in surgeries:
                ps_id = surgery.get('id')
                surgery_type_id = surgery.get('surgery_id')

                if not ps_id:
                    added_surgery = BillingSurgeries(billing_id=billing.id, surgery_id=surgery_type_id)
                    db.session.add(added_surgery)
                    db.session.flush()
                    total_amount += added_surgery.price
                else:
                    new_surg_ids.add(ps_id)

            to_delete_surgs = existing_surg_ids - new_surg_ids
            if to_delete_surgs:
                BillingSurgeries.query.filter(BillingSurgeries.id.in_(to_delete_surgs)).delete(
                    synchronize_session=False)

            # Tests update (unchanged)
            existing_tests = BillingTests.query.filter_by(billing_id=billing.id).all()
            existing_test_ids = {pt.id for pt in existing_tests}

            new_test_ids = set()
            for test in tests:
                pt_id = test.get('id')
                test_type_id = test.get('test_id')

                if not pt_id:
                    added_test = BillingTests(billing_id=billing.id, test_id=test_type_id)
                    db.session.add(added_test)
                    db.session.flush()
                    total_amount += added_test.price
                else:
                    new_test_ids.add(pt_id)

            to_delete_tests = existing_test_ids - new_test_ids
            if to_delete_tests:
                BillingTests.query.filter(BillingTests.id.in_(to_delete_tests)).delete(synchronize_session=False)

            billing.total_amount = total_amount
            db.session.commit()

            # If status changed to CANCELLED, revert stock
            if json_data.get("status") == "CANCELLED":
                for med in BillingMedicines.query.filter_by(billing_id=billing.id).all():
                    stock_record = MedicineStock.query.filter_by(medicine_id=med.medicine_id).first()
                    if stock_record:
                        stock_record.quantity += med.quantity
                db.session.commit()

            return billing_serializer.dump(billing), 200

        except ValueError as ve:
            db.session.rollback()
            return {"error": str(ve)}, 400
        except IntegrityError as ie:
            db.session.rollback()
            return {"error": str(ie.orig)}, 400
        except Exception as e:
            db.session.rollback()
            print(f"PUT /billing error: {e}")
            return {"error": "Internal error occurred"}, 500

    def delete(self):
        order_id = request.args.get("id")
        if not order_id:
            return {"error": "Order ID required"}, 400

        order = Billing.query.get(order_id)
        if not order:
            return {"error": "Order not found"}, 404

        BillingMedicines.query.filter_by(billing_id=order_id).delete()
        BillingTests.query.filter_by(billing_id=order_id).delete()
        BillingSurgeries.query.filter_by(billing_id=order_id).delete()

        db.session.delete(order)
        db.session.commit()
        return {"message": "Order deleted successfully"}, 200

    def patch(self):
        """
        Handles payment processing for an existing bill by calling the
        record_payment method on the Billing model.
        """
        try:
            json_data = request.get_json(force=True)
            bill_id = json_data.get("id")
            payment_amount = json_data.get("amount")
            payment_method = json_data.get("method")
            transaction_ref = json_data.get("transaction_ref")  # Optional

            if not bill_id or not payment_amount or not payment_method:
                return {"error": "Missing required fields: id, amount, and method."}, 400

            billing = Billing.query.get(bill_id)
            if not billing:
                return {"error": f"Bill with ID {bill_id} not found."}, 404

            # Handle None values for amount_paid
            if billing.amount_paid is None:
                billing.amount_paid = 0.0

            # --- CORE LOGIC: Record Payment ---
            applied_amount = billing.record_payment(
                payment_amount=payment_amount,
                payment_method=payment_method,
                transaction_ref=transaction_ref
            )
            # ----------------------------------

            db.session.commit()

            # Calculate remaining amount safely
            remaining_due = billing.total_amount - (billing.amount_paid or 0)

            return {
                "message": "Payment recorded successfully",
                "applied_amount": applied_amount,
                "new_status": billing.status,
                "amount_paid": billing.amount_paid,
                "total_due": remaining_due
            }, 200

        except ValueError as ve:
            # Catches errors like 'Amount already fully paid' or 'Payment must be positive'
            db.session.rollback()
            return {"error": str(ve)}, 400
        except Exception as e:
            db.session.rollback()
            print(f"Payment error: {e}")
            return {"error": "Internal error occurred during payment processing"}, 500
