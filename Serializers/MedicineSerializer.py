from extentions import ma
from Models.Medicine import Medicine
from Serializers.MedicineStockSerializer import medicine_stock_serializer

class MedicineSerializer(ma.SQLAlchemyAutoSchema):
    medicine_stock = ma.Nested(medicine_stock_serializer, many=True, dump_only=True)

    class Meta:
        model = Medicine
        load_instance = True

medicine_serializer = MedicineSerializer()
medicine_serializers = MedicineSerializer(many=True)
