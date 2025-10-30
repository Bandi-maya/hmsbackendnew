from marshmallow import fields

# from Serializers.LabRequestSerializers import LabRequestSerializer
from extentions import ma
from Models.LabReport import LabReport


class LabReportSerializer(ma.SQLAlchemyAutoSchema):
    # lab_request = fields.Nested(LabRequestSerializer, many=False)

    class Meta:
        model = LabReport
        load_instance = True
        include_fk = True


lab_report_serializer = LabReportSerializer()
lab_report_serializers = LabReportSerializer(many=True)
