from Models.OperationTheatre import OperationTheatre
from app_utils import ma

class OperationTheatreSerializer(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = OperationTheatre
        load_instance = True
        include_fk = True

operation_theatre_serializer = OperationTheatreSerializer()
operation_theatre_serializers = OperationTheatreSerializer(many=True)
