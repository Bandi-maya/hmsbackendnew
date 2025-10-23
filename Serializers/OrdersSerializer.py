from Models.Orders import Orders
from Serializers.PurchaseOrderSerializer import purchase_order_serializer
from Serializers.UserSerializers import user_serializer
from Serializers.PrescriptionSerializers import prescription_serializer
from Serializers.PurchaseTestSerializers import purchase_test_serializer
from Serializers.PurchaseSurgerySerializers import purchase_surgery_serializer
from extentions import ma

class OrdersSerializer(ma.SQLAlchemyAutoSchema):
    user = ma.Nested(user_serializer, dump_only=True)
    prescription = ma.Nested(prescription_serializer, dump_only=True)
    medicines = ma.Nested(purchase_order_serializer, many=True, dump_only=True)
    lab_tests = ma.Nested(purchase_test_serializer, many=True, dump_only=True) 
    surgeries = ma.Nested(purchase_surgery_serializer, many=True, dump_only=True) 

    class Meta:
        model = Orders
        load_instance = True
        include_fk = True

order_serializer = OrdersSerializer()
order_serializers = OrdersSerializer(many=True)
