import os
from uuid import uuid4
from flask import request, current_app, url_for
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from Models.AccountInfo import AccountInfo
from Serializers.AccountInfoSerializers import account_info_serializer
from app_utils import db


UPLOAD_FOLDER = "uploads"  # Local folder to store uploaded images


class AccountInfoResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        try:
            account = AccountInfo.query.get(1)
            if not account:
                return {"message": "No account info found."}, 404

            # Prepend host URL to logo path for client access
            logo_url = url_for('uploaded_file', filename=os.path.basename(account.logo_url), _external=True)
            data = account_info_serializer.dump(account)
            data['logo_url'] = logo_url

            return data, 200
        except Exception as e:
            print(e)
            return {"error": "Internal error occurred"}, 500

    def post(self):
        try:
            name = request.form.get("name")
            logo_file = request.files.get("logo")

            if not name or not logo_file:
                return {"error": "Both 'name' and 'logo' are required."}, 400

            # Validate image file
            if not logo_file.mimetype.startswith("image/"):
                return {"error": "Invalid file type. Only images are allowed."}, 400

            # Save the image with a unique filename
            filename = secure_filename(logo_file.filename)
            unique_filename = f"{uuid4().hex}_{filename}"
            save_path = os.path.join(UPLOAD_FOLDER, unique_filename)

            # Ensure the upload folder exists
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)

            logo_file.save(save_path)

            # Save to DB
            account = AccountInfo(name=name, logo_url=save_path)
            db.session.add(account)
            db.session.commit()

            # Return full URL for logo
            data = account_info_serializer.dump(account)
            data['logo_url'] = url_for('uploaded_file', filename=unique_filename, _external=True)

            return data, 201

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
            # Expect form data
            name = request.form.get("name")
            account_id = request.form.get("id")
            logo_file = request.files.get("logo")

            if not account_id:
                return {"error": "Missing 'id' in request"}, 400

            appointment = AccountInfo.query.get(account_id)
            if not appointment:
                return {"error": "AccountInfo not found"}, 404

            if name:
                appointment.name = name.strip()

            # If a new logo is uploaded
            if logo_file:
                if not logo_file.mimetype.startswith("image/"):
                    return {"error": "Invalid file type. Only images are allowed."}, 400

                filename = secure_filename(logo_file.filename)
                unique_filename = f"{uuid4().hex}_{filename}"
                save_path = os.path.join(UPLOAD_FOLDER, unique_filename)

                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                logo_file.save(save_path)

                # Optional: Delete old logo file
                old_path = appointment.logo_url
                if old_path and os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except Exception as e:
                        print(f"Warning: failed to delete old logo: {e}")

                appointment.logo_url = save_path

            db.session.commit()

            # Respond with full logo URL
            result = account_info_serializer.dump(appointment)
            result['logo_url'] = url_for('uploaded_file', filename=os.path.basename(appointment.logo_url),
                                         _external=True)

            return result, 200

        except IntegrityError as ie:
            db.session.rollback()
            return {"error": f"Database integrity error: {str(ie.orig)}"}, 400
        except ValueError as ve:
            db.session.rollback()
            return {"error": str(ve)}, 400
        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal error occurred"}, 500