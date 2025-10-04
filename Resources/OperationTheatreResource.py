from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from Models.OperationTheatre import OperationTheatre
from Serializers.OperationTheatreSerializers import operation_theatre_serializer, operation_theatre_serializers
from app_utils import db


class OperationTheatreResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        try:
            # Optionally support getting a single OT by ID
            theatre_id = request.args.get('id')
            if theatre_id:
                theatre = OperationTheatre.query.get(theatre_id)
                if not theatre:
                    return {"error": "Operation Theatre not found"}, 404
                return operation_theatre_serializer.dump(theatre), 200

            # Return all operation theatres
            theatres = OperationTheatre.query.all()
            return operation_theatre_serializers.dump(theatres), 200

        except Exception as e:
            print(e)
            return {"error": "Internal error occurred"}, 500

    def post(self):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            # Validate required fields
            name = json_data.get('name')
            department_id = json_data.get('department_id')

            if not name or not department_id:
                return {"error": "Missing required fields: name, department_id"}, 400

            # Check if OT name already exists (unique constraint)
            existing_ot = OperationTheatre.query.filter_by(name=name).first()
            if existing_ot:
                return {"error": f"Operation Theatre with name '{name}' already exists"}, 400

            theatre = OperationTheatre(
                name=name,
                building=json_data.get('building'),
                floor=json_data.get('floor'),
                wing=json_data.get('wing'),
                room_number=json_data.get('room_number'),
                department_id=department_id,
                status=json_data.get('status', 'Available'),
                is_active=json_data.get('is_active', True),
                notes=json_data.get('notes')
            )
            db.session.add(theatre)
            db.session.commit()

            return operation_theatre_serializer.dump(theatre), 201

        except IntegrityError as ie:
            db.session.rollback()
            return {"error": str(ie.orig)}, 400

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500

    def put(self):
        try:
            json_data = request.get_json(force=True)
            theatre_id = json_data.get('id')
            if not theatre_id:
                return {"error": "Operation Theatre ID required"}, 400

            theatre = OperationTheatre.query.get(theatre_id)
            if not theatre:
                return {"error": "Operation Theatre not found"}, 404

            # Update fields if present in input
            theatre.name = json_data.get('name', theatre.name)
            theatre.building = json_data.get('building', theatre.building)
            theatre.floor = json_data.get('floor', theatre.floor)
            theatre.wing = json_data.get('wing', theatre.wing)
            theatre.room_number = json_data.get('room_number', theatre.room_number)
            theatre.department_id = json_data.get('department_id', theatre.department_id)
            theatre.status = json_data.get('status', theatre.status)
            theatre.is_active = json_data.get('is_active', theatre.is_active)
            theatre.notes = json_data.get('notes', theatre.notes)

            db.session.commit()

            return operation_theatre_serializer.dump(theatre), 200

        except IntegrityError as ie:
            db.session.rollback()
            return {"error": str(ie.orig)}, 400

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500

    def delete(self):
        try:
            theatre_id = request.args.get('id')
            if not theatre_id:
                return {"error": "Operation Theatre ID required"}, 400

            theatre = OperationTheatre.query.get(theatre_id)
            if not theatre:
                return {"error": "Operation Theatre not found"}, 404

            db.session.delete(theatre)
            db.session.commit()

            return {"message": "Operation Theatre deleted successfully"}, 200

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500
