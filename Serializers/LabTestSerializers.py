from extentions import ma
from Models.LabTest import LabTest


class LabTestSerializer(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = LabTest
        load_instance = True
        include_fk = True


lab_test_serializer = LabTestSerializer()
lab_test_serializers = LabTestSerializer(many=True)
