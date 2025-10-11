from Models.Department import Department
from extentions import ma

class DepartmentSerializer(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Department
        load_instance = True
        include_fk = True

department_serializer = DepartmentSerializer()
department_serializers = DepartmentSerializer(many=True)
