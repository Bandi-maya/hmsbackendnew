# from marshmallow import fields
# from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

# from Serializers.LabTestSerializers import LabTestSerializer
# from Serializers.UserSerializers import UserSchema
# from extentions import db
# from Models.LabRequest import LabRequest


# class LabRequestSerializer(SQLAlchemyAutoSchema):
#     test = fields.Nested(LabTestSerializer, many=False)
#     patient = fields.Nested(UserSchema, many=False)
#     requester = fields.Nested(UserSchema, many=False)

#     class Meta:
#         model = LabRequest
#         load_instance = True
#         include_fk = True


# lab_request_serializer = LabRequestSerializer()
# lab_request_serializers = LabRequestSerializer(many=True)
