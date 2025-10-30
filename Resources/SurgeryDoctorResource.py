# import json
# import logging
# from flask import request
# from flask_jwt_extended import jwt_required
# from flask_restful import Resource
# from sqlalchemy import or_
# from sqlalchemy.exc import IntegrityError
# from new import with_tenant_session_and_user
# from utils.logger import log_activity

# from Models.SurgeryDoctor import SurgeryDoctor
# from Serializers.SurgeryDoctorSerializers import surgery_doctor_serializer, surgery_doctor_serializers

# logger = logging.getLogger(__name__)

# class SurgeryDoctorResource(Resource):
#     method_decorators = [jwt_required()]

#     # ✅ GET single or all surgery-doctor assignments
#     @with_tenant_session_and_user
#     def get(self, tenant_session, **kwargs):
#         try:
#             # 🔹 Optional single item fetch
#             sd_id = request.args.get('id')
#             if sd_id:
#                 record = tenant_session.query(SurgeryDoctor).get(sd_id)
#                 if not record:
#                     return {"error": "SurgeryDoctor record not found"}, 404
#                 return surgery_doctor_serializer.dump(record), 200

#             # 🔹 Pagination params
#             page = request.args.get("page", type=int)
#             limit = request.args.get("limit", type=int)

#             query = tenant_session.query(SurgeryDoctor)
#             q = request.args.get('q')
#             if q:
#                 query = query.filter(
#                     or_(
#                         SurgeryDoctor.surgery_id.ilike(f"%{q}%"),
#                         SurgeryDoctor.doctor_id.ilike(f"%{q}%"),
#                     )
#                 )
#             # 🔹 Query all records
#             total_records = query.count()

#             # 🔹 Apply pagination if both page and limit provided
#             if page is not None and limit is not None:
#                 if page < 1: page = 1
#                 if limit < 1: limit = 10
#                 query = query.offset((page - 1) * limit).limit(limit)
#             else:
#                 page = 1
#                 limit = total_records

#             records = query.all()
#             result = surgery_doctor_serializers.dump(records)

#             # 🔹 Log activity
#             log_activity("GET_SURGERY_DOCTORS", details=json.dumps({
#                 "count": len(result),
#                 "page": page,
#                 "limit": limit
#             }))

#             # 🔹 Structured response
#             return {
#                 "page": page,
#                 "limit": limit,
#                 "total_records": total_records,
#                 "total_pages": (total_records + limit - 1) // limit if limit else 1,
#                 "data": result
#             }, 200

#         except Exception:
#             logger.exception("Error fetching SurgeryDoctor records")
#             return {"error": "Internal error occurred"}, 500

#     # ✅ POST new assignment
#     @with_tenant_session_and_user
#     def post(self, tenant_session, **kwargs):
#         try:
#             json_data = request.get_json(force=True)
#             if not json_data:
#                 return {"error": "No input data provided"}, 400

#             surgery_id = json_data.get('surgery_id')
#             doctor_id = json_data.get('doctor_id')
#             role = json_data.get('role')

#             if not surgery_id or not doctor_id or not role:
#                 return {"error": "Missing required fields: surgery_id, doctor_id, role"}, 400

#             existing = tenant_session.query(SurgeryDoctor).filter_by(
#                 surgery_id=surgery_id, doctor_id=doctor_id, role=role
#             ).first()
#             if existing:
#                 return {"error": "This doctor-role is already assigned to the surgery"}, 400

#             SurgeryDoctor.tenant_session = tenant_session
#             record = SurgeryDoctor(
#                 surgery_id=surgery_id,
#                 doctor_id=doctor_id,
#                 role=role
#             )
#             tenant_session.add(record)
#             tenant_session.flush()
#             tenant_session.commit()

#             log_activity("CREATE_SURGERY_DOCTOR", details=json.dumps(surgery_doctor_serializer.dump(record)))

#             return surgery_doctor_serializer.dump(record), 201

#         except IntegrityError as ie:
#             tenant_session.rollback()
#             return {"error": f"Database integrity error: {str(ie.orig)}"}, 400
#         except Exception:
#             tenant_session.rollback()
#             logger.exception("Error creating SurgeryDoctor record")
#             return {"error": "Internal error occurred"}, 500

#     # ✅ PUT update assignment
#     @with_tenant_session_and_user
#     def put(self, tenant_session, **kwargs):
#         try:
#             json_data = request.get_json(force=True)
#             sd_id = json_data.get('id')
#             if not sd_id:
#                 return {"error": "SurgeryDoctor ID required"}, 400

#             record = tenant_session.query(SurgeryDoctor).get(sd_id)
#             if not record:
#                 return {"error": "SurgeryDoctor record not found"}, 404

#             for field in ['surgery_id', 'doctor_id', 'role']:
#                 if field in json_data:
#                     setattr(record, field, json_data[field])

#             tenant_session.commit()
#             log_activity("UPDATE_SURGERY_DOCTOR", details=json.dumps(surgery_doctor_serializer.dump(record)))

#             return surgery_doctor_serializer.dump(record), 200

#         except IntegrityError as ie:
#             tenant_session.rollback()
#             return {"error": f"Database integrity error: {str(ie.orig)}"}, 400
#         except Exception:
#             tenant_session.rollback()
#             logger.exception("Error updating SurgeryDoctor record")
#             return {"error": "Internal error occurred"}, 500

#     # ✅ DELETE assignment
#     @with_tenant_session_and_user
#     def delete(self, tenant_session, **kwargs):
#         try:
#             sd_id = request.args.get('id')
#             if not sd_id:
#                 return {"error": "SurgeryDoctor ID required"}, 400

#             record = tenant_session.query(SurgeryDoctor).get(sd_id)
#             if not record:
#                 return {"error": "SurgeryDoctor record not found"}, 404

#             deleted_data = surgery_doctor_serializer.dump(record)
#             tenant_session.delete(record)
#             tenant_session.commit()

#             log_activity("DELETE_SURGERY_DOCTOR", details=json.dumps(deleted_data))
#             return {"message": "SurgeryDoctor record deleted successfully"}, 200

#         except IntegrityError as ie:
#             tenant_session.rollback()
#             return {"error": f"Database integrity error: {str(ie.orig)}"}, 400
#         except Exception:
#             tenant_session.rollback()
#             logger.exception("Error deleting SurgeryDoctor record")
#             return {"error": "Internal error occurred"}, 500
