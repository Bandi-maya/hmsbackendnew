from Models.SurgeryType import SurgeryType
from app_utils import ma

class SurgeryTypeSerializer(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = SurgeryType
        load_instance = True
        include_fk = True

surgery_type_serializer = SurgeryTypeSerializer()
surgery_type_serializers = SurgeryTypeSerializer(many=True)
