from Models.Payments import Payment
from Models.OperationTheatre import OperationTheatre
from extentions import ma

class PaymentSerializer(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Payment
        load_instance = True
        include_fk = True

payment_serializer = PaymentSerializer()
payment_serializers = PaymentSerializer(many=True)
