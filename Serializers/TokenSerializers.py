from Models.Tokens import Token
from Serializers.UserSerializers import UserSchema

from extentions import ma

class TokenSerializer(ma.SQLAlchemyAutoSchema):
    doctor = ma.Nested(UserSchema)
    patient = ma.Nested(UserSchema)

    class Meta:
        model = Token
        load_instance = True
        include_fk = True

TokenSerializerz = TokenSerializer()
TokenSerializers = TokenSerializer(many=True)