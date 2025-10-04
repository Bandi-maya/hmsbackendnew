from Serializers.WardBedsSerializers import WardBedsSerializer
from app_utils import ma
from Models.Wards import Ward
from Serializers.DepartmentSerializers import department_serializer
from Serializers.UserSerializers import user_serializer

class WardSerializer(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Ward
        load_instance = True
        include_fk = True

    creator = ma.Nested(user_serializer, dump_only=True)
    beds = ma.Nested(WardBedsSerializer, many=True)
    department = ma.Nested(department_serializer, dump_only=True)

ward_serializer = WardSerializer()
ward_serializers = WardSerializer(many=True)
