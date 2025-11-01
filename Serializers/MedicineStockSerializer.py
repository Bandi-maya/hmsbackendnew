from extentions import ma
from Models.MedicineStock import MedicineStock
# from Serializers.MedicineSerializer import medicine_serializer

class MedicineStockSerializer(ma.SQLAlchemyAutoSchema):
    # medicine = ma.Nested(medicine_serializer, dump_only=True)

    class Meta:
        model = MedicineStock
        load_instance = True
        include_fk = True

medicine_stock_serializer = MedicineStockSerializer()
medicine_stock_serializers = MedicineStockSerializer(many=True)
