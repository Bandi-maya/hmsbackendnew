from Models.Orders import Orders
from Serializers.PurchaseOrderSerializer import purchase_order_serializer
from Serializers.UserSerializers import user_serializer
from extentions import ma

class OrdersSerializer(ma.SQLAlchemyAutoSchema):
    user = ma.Nested(user_serializer, dump_only=True)
    items = ma.Nested(purchase_order_serializer, many=True, dump_only=True)  # <-- include items here
    # purchase_orders = ma.Nested(purchase_order_serializer, many=True, dump_only=True)

    class Meta:
        model = Orders
        load_instance = True
        include_fk = True

order_serializer = OrdersSerializer()
order_serializers = OrdersSerializer(many=True)
