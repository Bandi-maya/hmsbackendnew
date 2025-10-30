# resources/account_info.py
import os
from uuid import uuid4
import psycopg2
from psycopg2 import sql
from flask import request, url_for, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from Models.AccountInfo import AccountInfo
from extentions import db
from migration_helper import run_tenant_migrations

UPLOAD_FOLDER = "uploads"


class AccountInfoResource(Resource):
    method_decorators = [jwt_required()]

    def get(self):
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

            page = request.args.get("page", type=int)
            limit = request.args.get("limit", type=int)

            query = AccountInfo.query
            q = request.args.get('q')
            if q:
                query = query.filter(
                    or_(
                        AccountInfo.name.ilike(f"%{q}%"),
                        AccountInfo.subdomain.ilike(f"%{q}%"),
                    )
                )

            total_records = query.count()
            if page is not None and limit is not None:
                page = max(1, page)
                limit = max(1, limit)
                query = query.offset((page - 1) * limit).limit(limit)
            else:
                page, limit = 1, total_records

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
            current_app.logger.error(e)
            return {"error": "An internal error occurred"}, 500

    @staticmethod
    def create_database_and_user(db_name, db_user, db_password):
        try:
            connection = psycopg2.connect(
                dbname="postgres",
                user=os.environ.get('SUPERUSER_DB_USER'),
                password=os.environ.get('SUPERUSER_DB_PASSWORD'),
                host=os.environ.get('DB_HOST')
            )
            connection.autocommit = True
            cursor = connection.cursor()

            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
            cursor.execute(sql.SQL("CREATE USER {} WITH PASSWORD %s").format(sql.Identifier(db_user)), [db_password])
            cursor.execute(sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(sql.Identifier(db_name), sql.Identifier(db_user)))
            cursor.close()
            connection.close()

            new_conn = psycopg2.connect(
                dbname=db_name,
                user=os.environ.get('SUPERUSER_DB_USER'),
                password=os.environ.get('SUPERUSER_DB_PASSWORD'),
                host=os.environ.get('DB_HOST')
            )
            new_conn.autocommit = True
            new_cursor = new_conn.cursor()
            new_cursor.execute(sql.SQL("GRANT USAGE, CREATE ON SCHEMA public TO {}").format(sql.Identifier(db_user)))
            new_cursor.close()
            new_conn.close()

        except Exception as e:
            current_app.logger.error(f"DB Creation Error: {e}")
            raise

    def _rollback_db_creation(self, db_name, db_user):
        try:
            connection = psycopg2.connect(
                dbname="postgres",
                user=os.environ.get('SUPERUSER_DB_USER'),
                password=os.environ.get('SUPERUSER_DB_PASSWORD'),
                host=os.environ.get('DB_HOST')
            )
            connection.autocommit = True
            cursor = connection.cursor()
            cursor.execute(sql.SQL("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s;"), [db_name])
            cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db_name)))
            cursor.execute(sql.SQL("DROP USER IF EXISTS {}").format(sql.Identifier(db_user)))
            cursor.close()
            connection.close()
        except Exception as e:
            current_app.logger.error(f"Rollback Error: {e}")

    def post(self):
        try:
            name = request.form.get("name")
            subdomain = request.form.get("subdomain")
            logo_file = request.files.get("logo")

            if not all([name, subdomain, logo_file]):
                return {"error": "Missing required fields: name, subdomain, logo."}, 400

            if AccountInfo.query.filter((AccountInfo.name == name) | (AccountInfo.subdomain == subdomain)).first():
                return {"error": "Tenant with the given name or subdomain already exists."}, 409

            filename = secure_filename(logo_file.filename)
            unique_filename = f"{uuid4().hex}_{filename}"
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            save_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            logo_file.save(save_path)

            uid = uuid4().hex[:8]
            db_name, db_user, db_password = f"tenant_{uid}", f"user_{uid}", uuid4().hex[:16]

            try:
                self.create_database_and_user(db_name, db_user, db_password)
                db_uri = f"postgresql://{db_user}:{db_password}@{os.environ.get('DB_HOST')}:5432/{db_name}"

                new_account = AccountInfo(name=name, subdomain=subdomain, db_uri=db_uri, logo_url=save_path)
                db.session.add(new_account)
                db.session.commit()

                run_tenant_migrations(db_uri, subdomain, name)

                return {"message": f"Account {name} created successfully.", "id": new_account.id}, 201
            except Exception as e:
                self._rollback_db_creation(db_name, db_user)
                raise e

        except IntegrityError:
            db.session.rollback()
            return {"error": "A tenant with that name or subdomain already exists."}, 400
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return {"error": f"An internal error occurred: {e}"}, 500

    def put(self):
        try:
            account_id = request.form.get("id")
            if not account_id:
                return {"error": "Missing 'id' in request"}, 400

            account = AccountInfo.query.get(account_id)
            if not account:
                return {"error": "AccountInfo not found"}, 404

            new_db_uri = request.form.get("db_uri")
            db_changed = new_db_uri and account.db_uri != new_db_uri

            if request.form.get("name"):
                account.name = request.form.get("name")
            if db_changed:
                account.db_uri = new_db_uri

            logo_file = request.files.get("logo")
            if logo_file:
                if account.logo_url and os.path.exists(account.logo_url):
                    try:
                        os.remove(account.logo_url)
                    except OSError as e:
                        current_app.logger.error(f"Error deleting old logo: {e}")

                filename = secure_filename(logo_file.filename)
                unique_filename = f"{uuid4().hex}_{filename}"
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                save_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                logo_file.save(save_path)
                account.logo_url = save_path

            if db_changed:
                # Run migrations before committing to avoid inconsistent state
                run_tenant_migrations(account.db_uri)

            db.session.commit()
            return {"message": f"Account {account.name} updated successfully."}, 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return {"error": f"An internal error occurred: {e}"}, 500

    # def delete(self):
    #     """
    #     Deletes a tenant account.
    #     """
    #     try:
    #         account_id = request.args.get('id')
    #         if not account_id:
    #             return {"error": "Missing 'id' in query parameter"}, 400

    #         account = AccountInfo.query.get(account_id)
    #         if not account:
    #             return {"error": "AccountInfo not found"}, 404

    #         # Optional: Delete the associated logo file from the server
    #         if account.logo_url and os.path.exists(account.logo_url):
    #             try:
    #                 os.remove(account.logo_url)
    #             except OSError as e:
    #                 print(f"Error deleting logo file during account deletion: {e}")

    #         db.session.delete(account)
    #         db.session.commit()

    #         return {"message": f"Account '{account.name}' deleted successfully."}, 200

    #     except Exception as e:
    #         db.session.rollback()
    #         print(e)
    #         return {"error": f"An internal error occurred: {e}"}, 500
