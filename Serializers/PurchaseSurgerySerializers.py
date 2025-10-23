from extentions import ma
from Models.PurchaseSurgery import PurchaseSurgery
from Serializers.SurgerySerializers import surgery_serializer
from Serializers.UserSerializers import user_serializer
from Serializers.SurgeryTypeSerializers import surgery_type_serializer
from Serializers.OperationTheatreSerializers import operation_theatre_serializer

class PurchaseSurgerySerializer(ma.SQLAlchemyAutoSchema):
    surgeries = ma.Nested(surgery_serializer, dump_only=True)
    surgery_type = ma.Nested(surgery_type_serializer, dump_only=True)
    operation_theatre=ma.Nested(operation_theatre_serializer, dump_only=True)

    class Meta:
        model = PurchaseSurgery
        load_instance = True
        include_fk = True

purchase_surgery_serializer = PurchaseSurgerySerializer()
purchase_surgery_serializers = PurchaseSurgerySerializer(many=True)
