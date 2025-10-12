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
from extentions import db
from migration_helper import run_tenant_migrations

UPLOAD_FOLDER = "uploads"


class AccountInfoResource(Resource):
    # method_decorators = [jwt_required()]
    def get(self):
        """
        Retrieves one or all tenant account info records.
        If an 'id' is provided in query params, it fetches a single tenant.
        Otherwise, it returns a paginated list of tenants.
        """
        try:
            account_id = request.args.get('id')
            if account_id:
                account = AccountInfo.query.get(account_id)
                if not account:
                    return {"message": "Account info not found for the given ID."}, 404

                data = {
                    "id": account.id,
                    "name": account.name,
                    "subdomain": account.subdomain,
                    "logo_url": url_for('uploaded_file', filename=os.path.basename(account.logo_url),
                                        _external=True) if account.logo_url else None
                }
                return data, 200

            # 🔹 Pagination params
            page = request.args.get("page", type=int)
            limit = request.args.get("limit", type=int)

            query = AccountInfo.query
            total_records = query.count()

            if page is not None and limit is not None:
                if page < 1: page = 1
                if limit < 1: limit = 10
                query = query.offset((page - 1) * limit).limit(limit)
            else:
                # If no pagination, return all records
                page = 1
                limit = total_records

            accounts = query.all()
            data = [{
                "id": acc.id,
                "name": acc.name,
                "subdomain": acc.subdomain,
                "logo_url": url_for('uploaded_file', filename=os.path.basename(acc.logo_url),
                                    _external=True) if acc.logo_url else None
            } for acc in accounts]

            return {
                "page": page,
                "limit": limit,
                "total_records": total_records,
                "total_pages": (total_records + limit - 1) // limit if limit else 1,
                "data": data
            }, 200

        except Exception as e:
            print(e)
            return {"error": "An internal error occurred"}, 500

    @staticmethod
    def create_database_and_user(db_name, db_user, db_password):
        """
            Creates a PostgreSQL database and user with full privileges,
            including schema access in the new database.
            """
        try:
            # Connect to the main 'postgres' database with a superuser
            connection = psycopg2.connect(
                dbname="postgres",
                user=os.environ.get('SUPERUSER_DB_USER'),
                password=os.environ.get('SUPERUSER_DB_PASSWORD'),
                host=os.environ.get('DB_HOST')
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
            new_conn = psycopg2.connect( # Use the same superuser for this temporary connection
                dbname=db_name,
                user=os.environ.get('SUPERUSER_DB_USER'),
                password=os.environ.get('SUPERUSER_DB_PASSWORD'),
                host=os.environ.get('DB_HOST')
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

    def _rollback_db_creation(self, db_name, db_user):
        """
        Drops a database and user to roll back a failed tenant creation.
        """
        try:
            connection = psycopg2.connect(
                dbname="postgres",
                user=os.environ.get('SUPERUSER_DB_USER'),
                password=os.environ.get('SUPERUSER_DB_PASSWORD'),
                host=os.environ.get('DB_HOST')
            )
            connection.autocommit = True
            cursor = connection.cursor()

            print(f"[Rollback] Attempting to drop database '{db_name}' and user '{db_user}'")
            # Terminate any active connections to the tenant DB before dropping it
            cursor.execute(sql.SQL("SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = %s;"), [db_name])

            cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db_name)))
            cursor.execute(sql.SQL("DROP USER IF EXISTS {}").format(sql.Identifier(db_user)))
            cursor.close()
            connection.close()
        except Exception as e:
            print(f"[Rollback Error] Could not clean up database '{db_name}' or user '{db_user}': {e}")

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

            existing_account = AccountInfo.query.filter((AccountInfo.name == name) | (AccountInfo.subdomain == subdomain)).first()
            if existing_account:
                field = "name" if existing_account.name == name else "subdomain"
                return {"error": f"A tenant with that {field} already exists."}, 409 # 409 Conflict is a good status code here

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

            # 2. Wrap the creation process in a try/except to handle rollbacks
            try:
                # --- Create Database and User ---
                self.create_database_and_user(db_name, db_user, db_password)

                # --- Construct DB URI with hardcoded host ---
                db_host = os.environ.get('DB_HOST')
                db_uri = f"postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name}"

                print("hi")
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
            except Exception as e:
                # If anything fails after this point, roll back the DB creation
                print(f"An error occurred during tenant setup. Rolling back database creation. Error: {e}")
                self._rollback_db_creation(db_name, db_user)
                # Re-raise the exception to be caught by the outer block for a 500 response
                raise

        except IntegrityError:
            db.session.rollback()
            return {"error": "A tenant with that name or subdomain may already exist."}, 400
        except Exception as e:
            db.session.rollback()
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
