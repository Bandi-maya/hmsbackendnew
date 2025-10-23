from Models.Wards import Ward
from Serializers.DepartmentSerializers import department_serializer
from Serializers.UserSerializers import user_serializer
from extentions import ma

class WardSerializer(ma.SQLAlchemyAutoSchema):
    beds = ma.Nested('WardBedsSerializer', many=True)  # 👈 Lazy reference here

    class Meta:
        model = Ward
        load_instance = True
        include_fk = True

    creator = ma.Nested(user_serializer, dump_only=True)
    department = ma.Nested(department_serializer, dump_only=True)

class WardSerializerForBed(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Ward
        load_instance = True
        include_fk = True

    department = ma.Nested(department_serializer, dump_only=True)

ward_serializer = WardSerializer()
ward_serializers = WardSerializer(many=True)
ward_serializer_for_bed = WardSerializerForBed()
