from app_utils import ma
from Models.UserField import UserField


class UserFieldSerializers(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = UserField
        load_instance = True
        include_fk = True


user_field_serializer = UserFieldSerializers()
user_field_serializers = UserFieldSerializers(many=True)
