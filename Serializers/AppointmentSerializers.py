from Models.Appointments import Appointment
from Serializers.UserSerializers import user_serializer
from extentions import ma

class AppointmentSerializer(ma.SQLAlchemyAutoSchema):
    doctor = ma.Nested(user_serializer, dump_only=True)
    patient = ma.Nested(user_serializer, dump_only=True)

    class Meta:
        model = Appointment
        load_instance = True
        include_fk = True

AppointmentSerializerz = AppointmentSerializer()
AppointmentSerializers = AppointmentSerializer(many=True)