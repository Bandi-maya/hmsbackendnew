from app_utils import ma
from Models.Prescriptions import Prescriptions
from Models.PrescriptionMedicines import PrescriptionMedicines
from Models.PrescriptionTests import PrescriptionTests

class PrescriptionMedicineSerializer(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = PrescriptionMedicines
        # load_instance = True
        include_fk = True

prescription_medicine_serializer = PrescriptionMedicineSerializer()
prescription_medicine_serializers = PrescriptionMedicineSerializer(many=True)

class PrescriptionTestsSerializer(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = PrescriptionTests
        # load_instance = True
        include_fk = True

prescription_test_serializer = PrescriptionTestsSerializer()
prescription_test_serializers = PrescriptionTestsSerializer(many=True)

class PrescriptionSerializer(ma.SQLAlchemyAutoSchema):
    medicines = ma.Nested(PrescriptionMedicineSerializer, many=True)
    tests = ma.Nested(PrescriptionTestsSerializer, many=True)
    
    class Meta:
        model = Prescriptions
        load_instance = True
        include_fk = True

prescription_serializer = PrescriptionSerializer()
prescription_serializers = PrescriptionSerializer(many=True)
