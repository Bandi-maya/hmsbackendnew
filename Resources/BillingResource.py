from flask import request
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from app_utils import db
from Serializers.BillingSerializers import billing_serializers, billing_serializer
from Models.Billing import Billing
from Models.BillingMedicines import BillingMedicines
from Models.BillingTests import BillingTests


class BillingResource(Resource):
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
            isMedicinesExists = False if not medicines or not isinstance(medicines, list) else True
            isTestsExists= False if not tests or not isinstance(tests, list) else True

            if not (isMedicinesExists or isTestsExists):
                return {"error": "Medicines or Tests are required for a billing"}
            
            total_amount = 0

            billing = Billing(patient_id=json_data.get('patient_id'), doctor_id=json_data.get('doctor_id'), notes=json_data.get('notes'), prescription_id=json_data.get('prescription_id'))
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
        isMedicinesExists = False if not medicines or not isinstance(medicines, list) else True
        isTestsExists= False if not tests or not isinstance(tests, list) else True
        
        if not (isMedicinesExists or isTestsExists):
            return {"error": "Medicines or Tests are required for a billing"}
            
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

        db.session.delete(order)
        db.session.commit()
        return {"message": "Order deleted successfully"}, 200
