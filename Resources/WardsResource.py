from flask import request
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from sqlalchemy.util import counter

from Models.WardBeds import WardBeds
from Models.Wards import Ward
from Serializers.WardSerializer import ward_serializer, ward_serializers
from app_utils import db

class WardsResource(Resource):
    def get(self):
        try:
            return ward_serializers.dump(Ward.query.all()), 200
        except Exception as e:
            print(e)
            return {"error": "Internal error occurred"}, 500

    def post(self):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            ward = Ward(**json_data)
            db.session.add(ward)
            db.session.flush()
            for bed_no in range(1, ward.capacity):
                ward_bed = WardBeds(ward_id=ward.id, bed_no=bed_no)
                db.session.add(ward_bed)
            db.session.commit()

            return ward_serializer.dump(ward), 201

        except ValueError as ve:
            db.session.rollback()
            return {"error": str(ve)}, 400

        except IntegrityError as ie:
            db.session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500

    def put(self):
        try:
            json_data = request.get_json(force=True)
            ward_id = json_data.get("id")
            if not ward_id:
                return {"error": "Ward ID is required"}, 400

            ward = Ward.query.get(ward_id)
            if not ward:
                return {"error": "Ward not found"}, 404

            ward_beds_count = WardBeds.query.filter_by(ward_id=ward_id).count()

            if ward_beds_count < ward.capacity:
                for bed_no in range(ward_beds_count + 1, ward.capacity + 1):
                    ward_bed = WardBeds(ward_id=ward.id, bed_no=bed_no)
                    db.session.add(ward_bed)

            elif ward_beds_count > ward.capacity:
                occupied_beds = WardBeds.query.filter(
                    WardBeds.ward_id == ward_id,
                    WardBeds.patient_id.isnot(None)
                ).count()

                if occupied_beds > ward.capacity:
                    raise ValueError("Ward has more occupied beds than its capacity")

                extra_beds_to_delete = ward_beds_count - ward.capacity

                unoccupied_beds = WardBeds.query.filter(
                    WardBeds.ward_id == ward_id,
                    WardBeds.patient_id.is_(None)
                ).order_by(WardBeds.bed_no.desc()).limit(extra_beds_to_delete).all()

                for bed in unoccupied_beds:
                    db.session.delete(bed)

            for key, value in json_data.items():
                if hasattr(ward, key):
                    setattr(ward, key, value)

            db.session.commit()
            return ward_serializer.dump(ward), 200

        except ValueError as ve:
            db.session.rollback()
            return {"error": str(ve)}, 400

        except IntegrityError as ie:
            db.session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500

    def delete(self):
        try:
            ward_id = request.args.get("id")
            if not ward_id:
                return {"error": "Ward ID is required"}, 400

            ward = Ward.query.get(ward_id)
            if not ward:
                return {"error": "Ward not found"}, 404

            db.session.delete(ward)
            db.session.commit()
            return {"message": "Ward deleted successfully"}, 200

        except IntegrityError as ie:
            db.session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500
