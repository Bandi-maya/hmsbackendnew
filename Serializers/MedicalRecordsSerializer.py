from Models.MedicalRecords import MedicalRecords
from Serializers.UserSerializers import user_serializer
from app_utils import ma

class MedicalRecordsSerializer(ma.SQLAlchemyAutoSchema):
    user = ma.Nested(user_serializer, dump_only=True)

    class Meta:
        model = MedicalRecords
        load_instance = True
        include_fk = True

medical_records_serializer = MedicalRecordsSerializer()
medical_records_serializers = MedicalRecordsSerializer(many=True)
