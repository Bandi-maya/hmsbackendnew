import logging

from flask import request
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from Models.Billing import Billing
from Models.BillingMedicines import BillingMedicines
from Models.BillingTests import BillingTests
from Serializers.BillingSerializers import billing_serializers, billing_serializer
from app_utils import db


class BillingResource(Resource):
    @staticmethod
    def _error_response(message, code=400):
        logging.error(message)
        return {"error": message}, code

    @staticmethod
    def _validate_items(items):
        return bool(items and isinstance(items, list))

    def get(self):
        try:
            return billing_serializers.dump(Billing.query.all()), 200
        except Exception as e:
            logging.exception(e)
            return self._error_response("Internal error occurred", 500)

    def post(self):
        json_data = request.get_json(force=True)
        if not json_data:
            return self._error_response("No input data provided")

        medicines = json_data.get("medicines")
        tests = json_data.get("tests")
        is_medicines_exists = self._validate_items(medicines)
        is_tests_exists = self._validate_items(tests)

        if not (is_medicines_exists or is_tests_exists):
            return self._error_response("Medicines or Tests are required for a billing")

        total_amount = 0
        try:
            billing = Billing(
                patient_id=json_data.get('patient_id'),
                doctor_id=json_data.get('doctor_id'),
                notes=json_data.get('notes'),
                prescription_id=json_data.get('prescription_id')
            )
            db.session.add(billing)
            db.session.flush()

            for medicine in medicines or []:
                added_medicine = BillingMedicines(
                    billing_id=billing.id,
                    medicine_id=medicine.get('medicine_id'),
                    quantity=medicine.get('quantity')
                )
                db.session.add(added_medicine)
                db.session.flush()
                total_amount += getattr(added_medicine, 'price', 0)

            for test in tests or []:
                added_test = BillingTests(
                    billing_id=billing.id,
                    test_id=test.get('test_id')
                )
                db.session.add(added_test)
                db.session.flush()
                total_amount += getattr(added_test, 'price', 0)

            billing.total_amount = total_amount
            db.session.commit()
            return billing_serializer.dump(billing), 201
        except ValueError as ve:
            db.session.rollback()
            return self._error_response(str(ve))
        except IntegrityError as ie:
            db.session.rollback()
            return self._error_response(str(ie.orig))
        except Exception as e:
            db.session.rollback()
            logging.exception(e)
            return self._error_response("Internal error occurred", 500)

    def put(self):
        json_data = request.get_json(force=True)
        order_id = json_data.get("id")
        if not order_id:
            return self._error_response("Prescription ID required")

        medicines = json_data.get("medicines")
        tests = json_data.get("tests")
        is_medicines_exists = self._validate_items(medicines)
        is_tests_exists = self._validate_items(tests)

        if not (is_medicines_exists or is_tests_exists):
            return self._error_response("Medicines or Tests are required for a billing")

        billing = Billing.query.get(order_id)
        if not billing:
            return self._error_response("Prescription not found", 404)

        for key, value in json_data.items():
            if hasattr(billing, key) and key in ['patient_id', 'doctor_id', 'notes', 'status']:
                setattr(billing, key, value)

        prescription_medicines = BillingMedicines.query.filter_by(billing_id=billing.id).all()
        medicine_ids = []
        for medicine in medicines or []:
            medicine_id = medicine.get('id')
            if not medicine_id:
                added_medicine = BillingMedicines(
                    billing_id=billing.id,
                    medicine_id=medicine.get('medicine_id'),
                    quantity=medicine.get('quantity')
                )
                db.session.add(added_medicine)
            else:
                medicine_ids.append(medicine_id)
                prescription_medicine_record = BillingMedicines.query.get(medicine_id)
                if medicine.get('quantity'):
                    setattr(prescription_medicine_record, 'quantity', medicine.get('quantity'))

        for prescription_medicine in prescription_medicines:
            if prescription_medicine.id not in medicine_ids:
                BillingMedicines.query.filter_by(id=prescription_medicine.id).delete()

        prescription_tests = BillingTests.query.filter_by(billing_id=billing.id).all()
        test_ids = []
        for test in tests or []:
            test_id = test.get('id')
            if not test_id:
                added_test = BillingTests(
                    billing_id=billing.id,
                    test_id=test.get('test_id')
                )
                db.session.add(added_test)
            else:
                test_ids.append(test_id)

        for prescription_test in prescription_tests:
            if prescription_test.id not in test_ids:
                BillingTests.query.filter_by(id=prescription_test.id).delete()

        db.session.commit()
        return billing_serializer.dump(billing), 200

    def delete(self):
        order_id = request.args.get("id")
        if not order_id:
            return self._error_response("Order ID required")

        order = Billing.query.get(order_id)
        if not order:
            return self._error_response("Order not found", 404)

        BillingMedicines.query.filter_by(billing_id=order_id).delete()
        BillingTests.query.filter_by(billing_id=order_id).delete()

        db.session.delete(order)
        db.session.commit()
        return {"message": "Order deleted successfully"}, 200
