import json
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import SQLAlchemyError
from Models.Emergencies import Emergency
from new import with_tenant_session_and_user
from utils.logger import log_activity
from Serializers.EmergenciesSerializers import emergencies_serializer, emergencies_serializers


class EmergencyResource(Resource):
    method_decorators = [jwt_required()]

    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        """Get all active emergency cases"""
        emergencies = tenant_session.query(Emergency)\
            .filter(Emergency.status == 'active')\
            .order_by(Emergency.created_at.desc())\
            .all()

        data = emergencies_serializers.dump(emergencies)

        log_activity("GET_EMERGENCIES", details=json.dumps({"count": len(data)}))
        return {"data": data}, 200

    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        """Add a new emergency case"""
        data = request.get_json()
        try:
            new_emergency = Emergency(
                patient_id=data.get("patient_id"),
                description=data.get("description"),
                severity=data.get("severity", "moderate"),
                status=data.get("status", "active"),
                admitted_to_ward=data.get("admitted_to_ward", False)
            )
            tenant_session.add(new_emergency)
            tenant_session.commit()

            log_activity("CREATE_EMERGENCY", details=json.dumps({"id": new_emergency.id}))
            return emergencies_serializer.dump(new_emergency), 201

        except SQLAlchemyError as e:
            tenant_session.rollback()
            return {"error": str(e)}, 500

    @with_tenant_session_and_user
    def put(self, tenant_session, emergency_id, **kwargs):
        """Update an existing emergency case"""
        data = request.get_json()
        try:
            emergency = tenant_session.query(Emergency).filter(Emergency.id == emergency_id).first()
            if not emergency:
                return {"error": "Emergency case not found"}, 404

            # Update fields if provided
            emergency.patient_id = data.get("patient_id", emergency.patient_id)
            emergency.description = data.get("description", emergency.description)
            emergency.severity = data.get("severity", emergency.severity)
            emergency.status = data.get("status", emergency.status)
            emergency.admitted_to_ward = data.get("admitted_to_ward", emergency.admitted_to_ward)

            tenant_session.commit()

            log_activity("UPDATE_EMERGENCY", details=json.dumps({"id": emergency.id}))
            return emergencies_serializer.dump(emergency), 200

        except SQLAlchemyError as e:
            tenant_session.rollback()
            return {"error": str(e)}, 500

    @with_tenant_session_and_user
    def delete(self, tenant_session, emergency_id, **kwargs):
        """Delete an emergency case"""
        try:
            emergency = tenant_session.query(Emergency).filter(Emergency.id == emergency_id).first()
            if not emergency:
                return {"error": "Emergency case not found"}, 404

            emergency.is_deleted = True
            emergency.status = 'inactive'
            tenant_session.commit()

            log_activity("DELETE_EMERGENCY", details=json.dumps({"id": emergency.id}))
            return {"message": "Emergency case deleted successfully"}, 200

        except SQLAlchemyError as e:
            tenant_session.rollback()
            return {"error": str(e)}, 500
