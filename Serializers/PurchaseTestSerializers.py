from extentions import ma
from Models.PurchaseTest import PurchaseTest
from Serializers.LabTestSerializers import lab_test_serializer

class PurchaseTestSerializer(ma.SQLAlchemyAutoSchema):
    lab_test = ma.Nested(lab_test_serializer, dump_only=True)

    class Meta:
        model = PurchaseTest
        load_instance = True
        include_fk = True

purchase_test_serializer = PurchaseTestSerializer()
purchase_test_serializers = PurchaseTestSerializer(many=True)
