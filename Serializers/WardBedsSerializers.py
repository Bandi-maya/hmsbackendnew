from Models.WardBeds import WardBeds
from Serializers.UserSerializers import UserSchema
from Serializers.WardSerializer import WardSerializer
# from Serializers.WardSerializer import WardSerializer
from extentions import ma

class WardBedsSerializer(ma.SQLAlchemyAutoSchema):
    patient = ma.Nested(UserSchema, dump_only=True)
    ward = ma.Nested(WardSerializer, dump_only=True)

    class Meta:
        model = WardBeds
        load_instance = True
        include_fk = True

ward_beds_serializer = WardBedsSerializer()
ward_beds_serializers = WardBedsSerializer(many=True)
