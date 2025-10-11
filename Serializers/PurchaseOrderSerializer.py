from extentions import ma
from Models.PurchaseOrder import PurchaseOrder
from Serializers.MedicineSerializer import medicine_serializer

class PurchaseOrderSerializer(ma.SQLAlchemyAutoSchema):
    medicine = ma.Nested(medicine_serializer, dump_only=True)

    class Meta:
        model = PurchaseOrder
        load_instance = True
        include_fk = True

purchase_order_serializer = PurchaseOrderSerializer()
purchase_order_serializers = PurchaseOrderSerializer(many=True)
