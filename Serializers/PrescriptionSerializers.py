# from Models.PrescritionSurgeries import PrescriptionSurgeries
# from Serializers.SurgerySerializers import SurgerySerializer
from Serializers.UserSerializers import user_serializer
from extentions import ma
from Models.Prescriptions import Prescriptions
# from Models.PrescriptionMedicines import PrescriptionMedicines
# from Models.PrescriptionTests import PrescriptionTests

# class PrescriptionMedicineSerializer(ma.SQLAlchemyAutoSchema):
#     class Meta:
#         model = PrescriptionMedicines
#         # load_instance = True
#         include_fk = True

# prescription_medicine_serializer = PrescriptionMedicineSerializer()
# prescription_medicine_serializers = PrescriptionMedicineSerializer(many=True)

# class PrescriptionSurgerySerializer(ma.SQLAlchemyAutoSchema):
#     surgery = ma.Nested(SurgerySerializer)
#     class Meta:
#         model = PrescriptionSurgeries
#         # load_instance = True
#         include_fk = True

# prescription_surgeries_serializer = PrescriptionSurgerySerializer()
# prescription_surgeries_serializers = PrescriptionSurgerySerializer(many=True)

# class PrescriptionTestsSerializer(ma.SQLAlchemyAutoSchema):
#     class Meta:
#         model = PrescriptionTests
#         # load_instance = True
#         include_fk = True

# prescription_test_serializer = PrescriptionTestsSerializer()
# prescription_test_serializers = PrescriptionTestsSerializer(many=True)

class PrescriptionSerializer(ma.SQLAlchemyAutoSchema):
    # medicines = ma.Nested(PrescriptionMedicineSerializer, many=True)
    # tests = ma.Nested(PrescriptionTestsSerializer, many=True)
    # surgeries = ma.Nested(PrescriptionSurgerySerializer, many=True)
    doctor = ma.Nested(user_serializer, dump_only=True)
    patient = ma.Nested(user_serializer, dump_only=True)

    class Meta:
        model = Prescriptions
        load_instance = True
        include_fk = True

prescription_serializer = PrescriptionSerializer()
prescription_serializers = PrescriptionSerializer(many=True)
