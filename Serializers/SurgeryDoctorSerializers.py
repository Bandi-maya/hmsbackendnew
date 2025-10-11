from Models.Surgery import Surgery
from Models.SurgeryDoctor import SurgeryDoctor
from extentions import ma

class SurgeryDoctorSerializer(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = SurgeryDoctor
        load_instance = True
        include_fk = True

surgery_doctor_serializer = SurgeryDoctorSerializer()
surgery_doctor_serializers = SurgeryDoctorSerializer(many=True)
