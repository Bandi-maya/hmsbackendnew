from Models.SurgeryType import SurgeryType
from Serializers.DepartmentSerializers import DepartmentSerializer
from extentions import ma

class SurgeryTypeSerializer(ma.SQLAlchemyAutoSchema):
    department = ma.Nested(DepartmentSerializer, dump_only=True)
    class Meta:
        model = SurgeryType
        load_instance = True
        include_fk = True

surgery_type_serializer = SurgeryTypeSerializer()
surgery_type_serializers = SurgeryTypeSerializer(many=True)
