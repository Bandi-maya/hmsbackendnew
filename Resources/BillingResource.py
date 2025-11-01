import logging

from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy import or_, func
from sqlalchemy.exc import IntegrityError

from Models.BillingSurgeries import BillingSurgeries
from Models.MedicineStock import MedicineStock
from Models.Billing import Billing
from Models.BillingMedicines import BillingMedicines
from Models.BillingTests import BillingTests
from Models.Orders import Orders
from Models.WardBeds import WardBeds
from Models.Users import User
from Serializers.BillingSerializers import billing_serializers, billing_serializer
from Serializers.OrdersSerializer import order_serializer
from new import with_tenant_session_and_user

logger = logging.getLogger(__name__)

class BillingResource(Resource):
    method_decorators = [jwt_required()]

    # ---------------- GET ----------------
    @with_tenant_session_and_user
    def get(self, tenant_session):
        try:
            query = tenant_session.query(Billing)
            query = query.outerjoin(Orders, Billing.order_id == Orders.id)
            query = query.outerjoin(User, User.id == Orders.user_id)
            query = query.outerjoin(WardBeds, Billing.bed_id == WardBeds.id)
            total_records = query.count()
            paid_records = query.filter(Billing.status == "PAID").count()
            total_revenue = (
                query.filter(Billing.status == "PAID")
                .with_entities(func.coalesce(func.sum(Billing.total_amount), 0))
                .scalar()
            )
            # 🔹 Pagination params (optional)
            page = request.args.get("page", type=int)
            limit = request.args.get("limit", type=int)

            q = request.args.get('q')
            if q:
                query = query.filter(
                    or_(
                        User.name.ilike(f"%{q}%"),
                        User.email.ilike(f"%{q}%"),
                        Billing.notes.ilike(f"%{q}%"),
                    )
                )
            status = request.args.get("status")
            if status: 
                query = query.filter(
                    or_(
                        Billing.status==status
                    )
                )

            # 🔹 Apply pagination if both page and limit are provided
            if page is not None and limit is not None:
                if page < 1: page = 1
                if limit < 1: limit = 10
                query = query.offset((page - 1) * limit).limit(limit)
            else:
                # Return all if pagination not provided
                page = 1
                limit = total_records

            billings = query.all()
            result = billing_serializers.dump(billings)

            # 🔹 Structured response
            return {
                "page": page,
                "limit": limit,
                "total_records": total_records,
                "paid_records": paid_records,
                "total_revenue": total_revenue,
                "total_pages": (total_records + limit - 1) // limit if limit else 1,
                "data": result
            }, 200

        except Exception as e:
            logger.exception("Error fetching billing records")
            return {"error": "Internal error occurred"}, 500

    # ---------------- POST ----------------
    @with_tenant_session_and_user
    def post(self, tenant_session):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400
            
            order_id = json_data.get('order_id')

            if not order_id:
                return {"error": "Order ID is mandatory"}, 400
            
            order = Orders.query.get(order_id)
            if not order:
                return {"error": "Order not found"}, 404
            order = order_serializer.dump(order)

            medicines = order.get('medicines', [])
            tests = order.get('lab_tests', [])
            surgeries = order.get('surgeries', [])
            total_amount = 0

            for med in medicines:
                stock_list = med.get('medicine_stock', [])
                if stock_list:
                    price = stock_list[0].get('price', 0)
                else:
                    price = 0
                quantity = med.get('quantity', 0)
                total_amount += price * quantity


            for test in tests:
                total_amount += test.get('lab_test').get('price', 0)
                
            for surgery in surgeries:
                total_amount += surgery.get('price', 0)
            billing = Billing(
                order_id=order_id,
                amount_paid=json_data.get('amount_paid', 0),
                total_amount=total_amount,
                notes=json_data.get('notes'),
            )
            tenant_session.add(billing)
            tenant_session.commit()

            return billing_serializer.dump(billing), 201

        except (ValueError, TypeError) as ve:
            tenant_session.rollback()
            return {"error": str(ve)}, 400
        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": str(ie.orig)}, 400
        except Exception as e:
            tenant_session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500

    # ---------------- PUT ----------------
    @with_tenant_session_and_user
    def put(self, tenant_session):
        try:
            json_data = request.get_json(force=True)
            billing_id = json_data.get("id")
            if not billing_id:
                return {"error": "Billing ID required"}, 400

            billing = tenant_session.query(Billing).get(billing_id)
            if not billing:
                return {"error": "Billing not found"}, 404

            # Update core fields
            for key in ['patient_id', 'doctor_id', 'notes', 'status']:
                if key in json_data and hasattr(billing, key):
                    setattr(billing, key, json_data[key])

            # TODO: add tenant-aware update logic for medicines, tests, surgeries

            tenant_session.commit()
            return billing_serializer.dump(billing), 200

        except Exception as e:
            tenant_session.rollback()
            print(f"PUT /billing error: {e}")
            return {"error": "Internal error occurred"}, 500

    # # ---------------- DELETE ----------------
    # @with_tenant_session_and_user
    # def delete(self, tenant_session):
    #     billing_id = request.args.get("id")
    #     if not billing_id:
    #         return {"error": "Billing ID required"}, 400

    #     billing = tenant_session.query(Billing).get(billing_id)
    #     if not billing:
    #         return {"error": "Billing not found"}, 404

    #     tenant_session.query(BillingMedicines).filter_by(billing_id=billing_id).delete()
    #     tenant_session.query(BillingTests).filter_by(billing_id=billing_id).delete()
    #     tenant_session.query(BillingSurgeries).filter_by(billing_id=billing_id).delete()
    #     tenant_session.delete(billing)
    #     tenant_session.commit()
    #     return {"message": "Billing deleted successfully"}, 200

    # # ---------------- PATCH (Payment) ----------------
    # @with_tenant_session_and_user
    # def patch(self, tenant_session):
    #     try:
    #         json_data = request.get_json(force=True)
    #         bill_id = json_data.get("id")
    #         payment_amount = json_data.get("amount")
    #         payment_method = json_data.get("method")
    #         transaction_ref = json_data.get("transaction_ref")

    #         if not bill_id or not payment_amount or not payment_method:
    #             return {"error": "Missing required fields: id, amount, method"}, 400

    #         billing = tenant_session.query(Billing).get(bill_id)
    #         if not billing:
    #             return {"error": f"Bill with ID {bill_id} not found"}, 404

    #         if billing.amount_paid is None:
    #             billing.amount_paid = 0.0

    #         applied_amount = billing.record_payment(
    #             payment_amount=payment_amount,
    #             payment_method=payment_method,
    #             transaction_ref=transaction_ref
    #         )
    #         tenant_session.commit()

    #         remaining_due = billing.total_amount - (billing.amount_paid or 0)
    #         return {
    #             "message": "Payment recorded successfully",
    #             "applied_amount": applied_amount,
    #             "new_status": billing.status,
    #             "amount_paid": billing.amount_paid,
    #             "total_due": remaining_due
    #         }, 200

    #     except ValueError as ve:
    #         tenant_session.rollback()
    #         return {"error": str(ve)}, 400
    #     except Exception as e:
    #         tenant_session.rollback()
    #         print(f"PATCH /billing error: {e}")
    #         return {"error": "Internal error occurred during payment processing"}, 500
