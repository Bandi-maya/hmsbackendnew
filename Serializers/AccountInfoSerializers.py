from Models.AccountInfo import AccountInfo
from app_utils import ma

class AccountInfoSerializers(ma.SQLAlchemyAutoSchema):

    class Meta:
        model = AccountInfo
        load_instance = True
        include_fk = True

account_info_serializer = AccountInfoSerializers()
account_info_serializers = AccountInfoSerializers(many=True)