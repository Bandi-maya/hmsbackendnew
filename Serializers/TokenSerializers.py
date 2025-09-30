from Models.Tokens import Token

from app_utils import ma

class TokenSerializer(ma.SQLAlchemyAutoSchema):
    # doctor = ma.Nested(user_serializer, dump_only=True/)
    # patient = ma.Nested(user_serializer, dump_only=True)

    class Meta:
        model = Token
        load_instance = True
        include_fk = True

TokenSerializerz = TokenSerializer()
TokenSerializers = TokenSerializer(many=True)