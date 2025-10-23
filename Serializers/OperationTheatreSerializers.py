from Models.OperationTheatre import OperationTheatre
from Serializers.DepartmentSerializers import DepartmentSerializer
from extentions import ma

class OperationTheatreSerializer(ma.SQLAlchemyAutoSchema):
    department = ma.Nested(DepartmentSerializer, dump_only=True)
    class Meta:
        model = OperationTheatre
        load_instance = True
        include_fk = True

operation_theatre_serializer = OperationTheatreSerializer()
operation_theatre_serializers = OperationTheatreSerializer(many=True)
