from Models.AccountInfo import AccountInfo
from extentions import db

class AccountInfoSerializers(ma.SQLAlchemyAutoSchema):

    class Meta:
        model = AccountInfo
        load_instance = True
        include_fk = True

account_info_serializer = AccountInfoSerializers()
account_info_serializers = AccountInfoSerializers(many=True)