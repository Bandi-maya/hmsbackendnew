from app_utils import ma
from Models.Medicine import Medicine

class MedicineSerializer(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Medicine
        load_instance = True

medicine_serializer = MedicineSerializer()
medicine_serializers = MedicineSerializer(many=True)
