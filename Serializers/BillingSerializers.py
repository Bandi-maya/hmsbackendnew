from app_utils import ma
from Models.Billing import Billing
from Models.BillingMedicines import BillingMedicines
from Models.BillingTests import BillingTests
from Serializers.UserSerializers import UserSchema

class BillingMedicineSerializer(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = BillingMedicines
        # load_instance = True
        include_fk = True

billing_medicine_serializer = BillingMedicineSerializer()
billing_medicine_serializers = BillingMedicineSerializer(many=True)

class BillingTestsSerializer(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = BillingTests
        # load_instance = True
        include_fk = True

billing_test_serializer = BillingTestsSerializer()
billing_test_serializers = BillingTestsSerializer(many=True)

class BillingSerializer(ma.SQLAlchemyAutoSchema):
    medicines = ma.Nested(BillingMedicineSerializer, many=True)
    tests = ma.Nested(BillingTestsSerializer, many=True)
    patient = ma.Nested(UserSchema, many=False)
    doctor = ma.Nested(UserSchema, many=False)
    
    class Meta:
        model = Billing
        load_instance = True
        include_fk = True

billing_serializer = BillingSerializer()
billing_serializers = BillingSerializer(many=True)
