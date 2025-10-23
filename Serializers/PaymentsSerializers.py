from Models.Payments import Payment
from extentions import ma
from Serializers.BillingSerializers import BillingSerializer

class PaymentSerializer(ma.SQLAlchemyAutoSchema):
    billing = ma.Nested(BillingSerializer, dump_only=True)

    class Meta:
        model = Payment
        load_instance = True
        include_fk = True

payment_serializer = PaymentSerializer()
payment_serializers = PaymentSerializer(many=True)
