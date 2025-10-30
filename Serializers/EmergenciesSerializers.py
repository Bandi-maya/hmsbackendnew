from Models.Emergencies import Emerygency
from extentions import ma

class EmergenciesSerializers(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Emerygency
        load_instance = True
        include_fk = True

emergencies_serializer = EmergenciesSerializers()
emergencies_serializers = EmergenciesSerializers(many=True)
