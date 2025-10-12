import json
import logging
from flask import request
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from new import with_tenant_session_and_user
from utils.logger import log_activity

from Models.Billing import Billing
from Models.Payments import Payment
from Serializers.PaymentsSerializers import payment_serializers

logger = logging.getLogger(__name__)

class BillingPaymentResource(Resource):
    # ✅ POST a new payment
    @with_tenant_session_and_user
    def post(self, tenant_session, billing_id, **kwargs):
        data = request.get_json()
        amount = data.get("amount")
        method = data.get("method")
        transaction_ref = data.get("transaction_ref")

        if not amount or not method:
            return {"error": "Amount and method are required fields."}, 400

        billing = tenant_session.query(Billing).get(billing_id)
        if not billing:
            return {"error": f"Billing with ID {billing_id} not found."}, 404

        remaining = billing.total_amount - (billing.amount_paid or 0)
        if remaining <= 0:
            return {"error": "Billing already fully paid."}, 400
        if amount > remaining:
            return {"error": f"Payment amount ({amount}) exceeds remaining balance ({remaining})."}, 400

        try:
            Payment.tenant_session = tenant_session
            payment = Payment(
                billing_id=billing.id,
                amount=amount,
                method=method,
                transaction_ref=transaction_ref
            )
            tenant_session.add(payment)
            tenant_session.flush()

            billing.update_status_based_on_payments()
            tenant_session.commit()

            log_activity("CREATE_BILLING_PAYMENT", details=json.dumps({
                "billing_id": billing.id,
                "payment": {
                    "id": payment.id,
                    "amount": payment.amount,
                    "method": payment.method,
                    "transaction_ref": payment.transaction_ref,
                    "timestamp": payment.timestamp.isoformat()
                }
            }))

            return {
                "message": "Payment recorded successfully.",
                "payment": {
                    "id": payment.id,
                    "amount": payment.amount,
                    "method": payment.method,
                    "transaction_ref": payment.transaction_ref,
                    "timestamp": payment.timestamp.isoformat(),
                    "billing_id": billing.id,
                    "new_status": billing.status,
                    "total_paid": billing.amount_paid
                }
            }, 201

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400
        except Exception:
            tenant_session.rollback()
            logger.exception("Error recording payment")
            return {"error": "Internal error occurred"}, 500

    # ✅ GET payments for a billing record
    @with_tenant_session_and_user
    def get(self, tenant_session, billing_id=None, **kwargs):
        try:
            if billing_id:
                billing = tenant_session.query(Billing).get(billing_id)
                if not billing:
                    return {"error": f"Billing with ID {billing_id} not found."}, 404

                payments = billing.payments
                return {
                    "billing_id": billing.id,
                    "total_amount": billing.total_amount,
                    "amount_paid": billing.amount_paid,
                    "status": billing.status,
                    "payments": [
                        {
                            "id": p.id,
                            "amount": p.amount,
                            "method": p.method,
                            "transaction_ref": p.transaction_ref,
                            "timestamp": p.timestamp.isoformat()
                        } for p in payments
                    ]
                }, 200

            all_payments = tenant_session.query(Payment).all()
            return payment_serializers.dump(all_payments), 200

        except Exception:
            logger.exception("Error fetching payments")
            return {"error": "Internal error occurred"}, 500
