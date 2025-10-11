# resources/account_info.py
# API Resource for managing AccountInfo (tenants).

import os
from uuid import uuid4

import psycopg2
from psycopg2 import sql
from flask import request, url_for, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required

from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from Models.AccountInfo import AccountInfo
from app_utils import db
from migration_helper import run_tenant_migrations

UPLOAD_FOLDER = "uploads"


class AccountInfoResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
        """
        Retrieves one or all tenant account info records.
        If an 'id' is provided in query params, it fetches a single tenant.
        Otherwise, it returns a list of all tenants.
        """
        try:
            account_id = request.args.get('id')
            if account_id:
                account = AccountInfo.query.get(account_id)
                if not account:
                    return {"message": "Account info not found for the given ID."}, 404
                # data = account_info_serializer.dump(account)
                # For demonstration if serializer is not set up:
                data = {
                    "id": account.id,
                    "name": account.name,
                    "subdomain": account.subdomain,
                    "logo_url": url_for('uploaded_file', filename=os.path.basename(account.logo_url),
                                        _external=True) if account.logo_url else None
                }
                return data, 200
            else:
                accounts = AccountInfo.query.all()
                # data = account_info_serializer.dump(accounts, many=True)
                # For demonstration if serializer is not set up:
                data = [{
                    "id": acc.id,
                    "name": acc.name,
                    "subdomain": acc.subdomain,
                    "logo_url": url_for('uploaded_file', filename=os.path.basename(acc.logo_url),
                                        _external=True) if acc.logo_url else None
                } for acc in accounts]
                return data, 200
        except Exception as e:
            print(e)
            return {"error": "An internal error occurred"}, 500

    def create_database_and_user(self, db_name, db_user, db_password):
        """
            Creates a PostgreSQL database and user with full privileges,
            including schema access in the new database.
            """
        try:
            # Connect to the main 'postgres' database with a superuser
            connection = psycopg2.connect(
                dbname="postgres",
                user="hms",
                password="hms_main_123",  # Use your actual superuser password
                host="91.108.104.49"
            )
            connection.autocommit = True
            cursor = connection.cursor()

            # Create the new database
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))

            # Create the new user
            cursor.execute(
                sql.SQL("CREATE USER {} WITH PASSWORD %s").format(sql.Identifier(db_user)),
                [db_password]
            )

            # Grant all privileges on the database to the user
            cursor.execute(
                sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
                    sql.Identifier(db_name), sql.Identifier(db_user))
            )

            cursor.close()
            connection.close()

            # ✅ Connect to the new database to set up schema privileges
            new_conn = psycopg2.connect(
                dbname=db_name,
                user="hms",
                password="hms_main_123",
                host="91.108.104.49"
            )
            new_conn.autocommit = True
            new_cursor = new_conn.cursor()

            # Grant usage and create privileges on the public schema
            new_cursor.execute(
                sql.SQL("GRANT USAGE, CREATE ON SCHEMA public TO {}").format(sql.Identifier(db_user))
            )

            new_cursor.close()
            new_conn.close()

            print(f"[DB Created] Database '{db_name}' and user '{db_user}' created successfully.")

        except Exception as e:
            print(f"[DB Creation Error] {e}")
            raise

    def post(self):
        """
        Creates a new tenant account, generates a UID-based DB, and runs migrations.
        """
        try:
            print(request.form)
            name = request.form.get("name")
            subdomain = request.form.get("subdomain")
            logo_file = request.files.get("logo")

            if not all([name, subdomain, logo_file]):
                return {"error": "Missing required fields: name, subdomain, logo."}, 400

            # --- File Handling ---
            filename = secure_filename(logo_file.filename)
            unique_filename = f"{uuid4().hex}_{filename}"
            save_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            logo_file.save(save_path)

            # --- Generate UID and DB Credentials ---
            uid = uuid4().hex[:8]
            db_name = f"tenant_{uid}"
            db_user = f"user_{uid}"
            db_password = uuid4().hex[:16]

            # --- Create Database and User ---
            self.create_database_and_user(db_name, db_user, db_password)

            # --- Construct DB URI ---
            db_uri = f"postgresql://{db_user}:{db_password}@91.108.104.49:5432/{db_name}"

            # --- Save Tenant Info ---
            new_account = AccountInfo(
                name=name,
                subdomain=subdomain,
                db_uri=db_uri,
                logo_url=save_path
            )
            db.session.add(new_account)
            db.session.commit()

            # --- Run Migrations on New DB ---
            run_tenant_migrations(db_uri, subdomain, name)

            return {
                "message": f"Account for {new_account.name} created and database migrated.",
                "id": new_account.id
            }, 201

        except IntegrityError:
            db.session.rollback()
            return {"error": "A tenant with that name or subdomain may already exist."}, 400
        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": f"An internal error occurred: {e}"}, 500

    def put(self):
        """
        Updates a tenant account. If the db_uri is changed, it runs migrations.
        """
        try:
            account_id = request.form.get("id")
            if not account_id:
                return {"error": "Missing 'id' in request"}, 400

            account = AccountInfo.query.get(account_id)
            if not account:
                return {"error": "AccountInfo not found"}, 404

            # --- Check if db_uri is being updated ---
            new_db_uri = request.form.get("db_uri")
            db_changed = new_db_uri and account.db_uri != new_db_uri

            # Update other fields...
            if request.form.get("name"):
                account.name = request.form.get("name")
            if new_db_uri:
                account.db_uri = new_db_uri

            # ... (add file update logic here if needed for logo)
            logo_file = request.files.get("logo")
            if logo_file:
                # Optional: Delete old logo file
                if account.logo_url and os.path.exists(account.logo_url):
                    try:
                        os.remove(account.logo_url)
                    except OSError as e:
                        print(f"Error deleting old file: {e}")

                filename = secure_filename(logo_file.filename)
                unique_filename = f"{uuid4().hex}_{filename}"
                save_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                logo_file.save(save_path)
                account.logo_url = save_path

            db.session.commit()

            # --- Run migrations only if the database URI has changed ---
            if db_changed:
                run_tenant_migrations(account.db_uri)

            return {"message": f"Account {account.name} updated successfully."}, 200

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": f"An internal error occurred: {e}"}, 500

    def delete(self):
        """
        Deletes a tenant account.
        """
        try:
            account_id = request.args.get('id')
            if not account_id:
                return {"error": "Missing 'id' in query parameter"}, 400

            account = AccountInfo.query.get(account_id)
            if not account:
                return {"error": "AccountInfo not found"}, 404

            # Optional: Delete the associated logo file from the server
            if account.logo_url and os.path.exists(account.logo_url):
                try:
                    os.remove(account.logo_url)
                except OSError as e:
                    print(f"Error deleting logo file during account deletion: {e}")

            db.session.delete(account)
            db.session.commit()

            return {"message": f"Account '{account.name}' deleted successfully."}, 200

        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": f"An internal error occurred: {e}"}, 500

