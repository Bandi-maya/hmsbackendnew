from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from Models.BillingSurgeries import BillingSurgeries
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
            isMedicinesExists = False if not medicines or not isinstance(medicines, list) else True
            isTestsExists= False if not tests or not isinstance(tests, list) else True
            isSurgeriesExists= False if not surgeries or not isinstance(surgeries, list) else True

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
                billing = Billing(patient_id=json_data.get('patient_id'), notes=json_data.get('notes'), prescription_id=json_data.get('prescription_id'))
                db.session.add(billing)
                db.session.flush()

            for medicine in medicines:
                added_medicine = BillingMedicines(billing_id=billing.id, medicine_id=medicine.get('medicine_id'), quantity=medicine.get('quantity'))
                db.session.add(added_medicine)
                db.session.flush()
                total_amount += added_medicine.price

            for test in tests:
                added_test = BillingTests(billing_id=billing.id, test_id=test.get('test_id'))
                db.session.add(added_test)
                db.session.flush()
                total_amount += added_test.price

            for surgery in surgeries:
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
        json_data = request.get_json(force=True)
        order_id = json_data.get("id")
        if not order_id:
            return {"error": "Prescription ID required"}, 400
        
        medicines = json_data.get("medicines")
        tests = json_data.get("tests")
        surgeries = json_data.get("surgeries")
        isMedicinesExists = False if not medicines or not isinstance(medicines, list) else True
        isTestsExists= False if not tests or not isinstance(tests, list) else True
        isSurgeriesExists= False if not surgeries or not isinstance(surgeries, list) else True

        if not (isMedicinesExists or isTestsExists or isSurgeriesExists):
            return {"error": "Medicines or Tests or Surgeries are required for a billing"}
            
        billing = Billing.query.get(order_id)
        if not billing:
            return {"error": "Prescription not found"}, 404

        for key, value in json_data.items():
            if hasattr(billing, key) and key in ['patient_id', 'doctor_id', 'notes', 'status']:
                setattr(billing, key, value)

        prescription_medicines = BillingMedicines.query.filter_by(billing_id=billing.id).all()

        medicine_ids = []
        for medicine in medicines:
            medicine_id = medicine.get('id')
            if not medicine_id:
                added_medicine = BillingMedicines(billing_id=billing.id, medicine_id=medicine.get('medicine_id'), quantity=medicine.get('quantity'))
                db.session.add(added_medicine)
            else:
                medicine_ids.append(medicine_id)
                prescription_medicine_record = BillingMedicines.query.get(medicine_id)
                if medicine.get('quantity'):
                    setattr(prescription_medicine_record, 'quantity', medicine.get('quantity'))


        for prescription_medicine in prescription_medicines:
            if prescription_medicine.id not in medicine_ids:
                BillingMedicines.query.filter_by(id=prescription_medicine.id).delete()

        prescription_surgeries = BillingSurgeries.query.filter_by(billing_id=billing.id).all()

        surgery_ids = []
        for surgery in surgeries:
            surgery_id = surgery.get('id')
            if not surgery_id:
                added_surgery = BillingSurgeries(billing_id=billing.id, surgery_id=surgery.get('surgery_id'))
                db.session.add(added_surgery)
            else:
                surgery_ids.append(surgery_id)

        for prescription_surgery in prescription_surgeries:
            if prescription_surgery.id not in surgery_ids:
                BillingSurgeries.query.filter_by(id=prescription_surgery.id).delete()

        prescription_tests = BillingTests.query.filter_by(billing_id=billing.id).all()
        
        test_ids = []
        for test in tests:
            test_id = test.get('id')
            if not test_id:
                added_test = BillingTests(billing_id=billing.id, test_id=test.get('test_id'))
                db.session.add(added_test)
            else:
                test_ids.append(test_id)

        for prescription_test in prescription_tests:
            if prescription_test.id not in test_ids:
                BillingMedicines.query.filter_by(id=prescription_test.id).delete()

        db.session.commit()
        return billing_serializer.dump(billing), 200

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
