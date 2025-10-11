from Models.WardBeds import WardBeds
from extentions import ma

class WardBedsSerializer(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = WardBeds
        load_instance = True
        include_fk = True

ward_beds_serializer = WardBedsSerializer()
ward_beds_serializers = WardBedsSerializer(many=True)
