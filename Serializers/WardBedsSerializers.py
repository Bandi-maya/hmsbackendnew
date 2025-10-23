from Models.WardBeds import WardBeds
from Serializers.UserSerializers import UserSchema
from extentions import ma
from Serializers.WardSerializer import WardSerializerForBed 

class WardBedsSerializer(ma.SQLAlchemyAutoSchema):
    patient = ma.Nested(UserSchema, dump_only=True)
    ward = ma.Nested(WardSerializerForBed, dump_only=True)  # ✅ Use the safe serializer

    class Meta:
        model = WardBeds
        load_instance = True
        include_fk = True

ward_beds_serializer = WardBedsSerializer()
ward_beds_serializers = WardBedsSerializer(many=True)
