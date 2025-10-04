from flask import request
from flask_restful import Resource

from Serializers.PaymentsSerializers import payment_serializers
from app_utils import db
from Models.Billing import Billing
from Models.Payments import Payment

class BillingPaymentResource(Resource):
    def post(self, billing_id):
        """
        Create a new payment for a billing record
        Endpoint: POST /billing/<int:billing_id>/payments
        Body: {
            "amount": 100.0,
            "method": "cash",
            "transaction_ref": "TXN123456" (optional)
        }
        """
        data = request.get_json()

        amount = data.get("amount")
        method = data.get("method")
        transaction_ref = data.get("transaction_ref")

        if not amount or not method:
            return {"error": "Amount and method are required fields."}, 400

        billing = Billing.query.get_or_404(billing_id)

        remaining = billing.total_amount - (billing.amount_paid or 0)
        if remaining <= 0:
            return {"error": "Billing already fully paid."}, 400

        if amount > remaining:
            return {"error": f"Payment amount ({amount}) exceeds remaining balance ({remaining})."}, 400

        try:
            payment = Payment(
                billing_id=billing.id,
                amount=amount,
                method=method,
                transaction_ref=transaction_ref
            )

            db.session.add(payment)
            db.session.flush()  # So we can update billing before commit

            billing.update_status_based_on_payments()
            db.session.commit()

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

        except Exception as e:
            db.session.rollback()
            return {"message": str(e)}, 500

    def get(self, billing_id=None):
        """
        Get all payments for a billing record
        Endpoint: GET /billing/<int:billing_id>/payments
        """
        if billing_id:
            billing = Billing.query.get_or_404(billing_id)
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
                    }
                    for p in payments
                ]
            }, 200

        return payment_serializers.dump(Payment.query.all())