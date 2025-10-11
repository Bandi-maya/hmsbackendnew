from Models.UserType import UserType
from extentions import ma


class UserTypeSerializer(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = UserType
        load_instance = True
        include_fk = True

user_type_serializer = UserTypeSerializer()
user_type_serializers = UserTypeSerializer(many=True)