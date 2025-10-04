from Models.Surgery import Surgery
from app_utils import ma

class SurgerySerializer(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Surgery
        load_instance = True
        include_fk = True

surgery_serializer = SurgerySerializer()
surgery_serializers = SurgerySerializer(many=True)
