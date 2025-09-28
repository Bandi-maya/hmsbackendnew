from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields

from Models.UserExtraFields import UserExtraFields
from Models.Users import User
from Serializers.DepartmentSerializers import DepartmentSerializer
from Serializers.UserTypeSerializer import UserTypeSerializer


class UserExtraFieldsSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserExtraFields
        load_instance = True
        include_fk = True

class UserSchema(SQLAlchemyAutoSchema):
    extra_fields = fields.Nested(UserExtraFieldsSchema, many=False)
    user_type = fields.Nested(UserTypeSerializer, many=False)
    department = fields.Nested(DepartmentSerializer, many=False)

    class Meta:
        model = User
        load_instance = True
        include_fk = True

user_serializer = UserSchema()
user_serializers = UserSchema(many=True)
