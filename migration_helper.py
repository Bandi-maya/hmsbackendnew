# from flask import current_app
# from flask_migrate import upgrade
# from sqlalchemy import create_engine, text
# from sqlalchemy.orm import sessionmaker
# import os
#
# from Models.Department import Department
# from Models.UserField import UserField, FieldTypeEnum
# from Models.UserType import UserType
# from Models.Users import User
#
#
# def run_tenant_migrations(db_uri, sub_domain, name):
#     """
#     Runs migrations on a tenant DB and inserts a default user.
#     """
#
#     app = current_app._get_current_object()
#
#     original_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
#     original_binds = app.config.get('SQLALCHEMY_BINDS')
#
#     migrations_dir = os.path.join(app.root_path, 'migrations')
#     if not os.path.exists(migrations_dir):
#         raise Exception("Migrations directory not found. Run 'flask db init' first.")
#
#     try:
#         # Point SQLAlchemy to the tenant DB
#         app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
#         app.config.pop('SQLALCHEMY_BINDS', None)
#
#         print(f"Running migrations for tenant DB: {db_uri}")
#
#         alembic_cfg = Config(alembic_ini_path)
#         alembic_cfg.set_main_option('sqlalchemy.url', db_uri)
#
#         # Run Alembic upgrade to head on tenant DB
#         command.upgrade(alembic_cfg, 'head')
#         print("Migrations completed successfully.")
#         #
#         # # --- Create all user types ---
#         # session.execute(text("""
#         #     INSERT INTO user_type (type, description)
#         #     VALUES
#         #         ('Admin', 'Administrator'),
#         #         ('Doctor', 'Medical Doctor'),
#         #         ('Patient', 'Patient'),
#         #         ('Nurse', 'Nursing Staff'),
#         #         ('Receptionist', 'Front Desk'),
#         #         ('LabTechnician', 'Lab Technician'),
#         #         ('Pharmacist', 'Pharmacy Staff');
#         # """))
#         #
#         # session.execute(text("""
#         #     INSERT INTO user_field (user_type, field_name, field_type, is_mandatory)
#         #     VALUES
#         #         (2, 'first_name', 'STRING', TRUE),
#         #         (2, 'last_name', 'STRING', TRUE),
#         #         (2, 'experience', 'INTEGER', FALSE),
#         #         (2, 'specialization', 'STRING', TRUE),
#         #         (3, 'first_name', 'STRING', TRUE),
#         #         (3, 'last_name', 'STRING', TRUE),
#         #         (3, 'disease', 'STRING', FALSE),
#         #         (3, 'notes', 'STRING', FALSE),
#         #         (3, 'assigned_to_doctor', 'INTEGER', FALSE),
#         #         (4, 'first_name', 'STRING', TRUE),
#         #         (4, 'last_name', 'STRING', TRUE),
#         #         (5, 'first_name', 'STRING', TRUE),
#         #         (5, 'last_name', 'STRING', TRUE),
#         #         (6, 'first_name', 'STRING', TRUE),
#         #         (6, 'last_name', 'STRING', TRUE),
#         #         (7, 'first_name', 'STRING', TRUE),
#         #         (7, 'last_name', 'STRING', TRUE);
#         # """))
#         #
#         # # Insert Department (returning the new id)
#         # result = session.execute(text("""
#         #     INSERT INTO department (name, description)
#         #     VALUES ('Admin Department', 'Created for admin')
#         #     RETURNING id
#         # """))
#         # department_id = result.scalar_one()  # Get the new department ID
#         #
#         # # Check if default user already exists
#         # existing_user = session.execute(text("""
#         #     SELECT 1 FROM "user" WHERE email = :email LIMIT 1
#         # """), {"email": "admin@tenant.com"}).scalar()
#
#         # if not existing_user:
#             # Insert default admin user
#             # session.execute(text("""
#             #     INSERT INTO "user" (
#             #         name, phone_no, date_of_birth, age, gender, address, blood_type,
#             #         department_id, user_type_id, email, username, password
#             #     )
#             #     VALUES (
#             #         :name, :phone_no, :date_of_birth, :age, :gender, :address, :blood_type,
#             #         :department_id, :user_type_id, :email, :username, :password
#             #     )
#             # """), {
#             #     "name": "Admin",
#             #     "phone_no": "123456",
#             #     "date_of_birth": "2000-10-10",  # Prefer ISO format for dates
#             #     "age": 20,
#             #     "gender": "MALE",
#             #     "address": "45677",
#             #     "blood_type": "A+",
#             #     "department_id": department_id,
#             #     "user_type_id": 1,
#             #     "email": f"{name}@{sub_domain}.com",
#             #     "username": f"{name}@{sub_domain}.com",
#             #     "password": "admin123",  # ⚠️ Remember to hash passwords in production!
#             # })
#         session.commit()
#         #     print("✅ Default admin user created.")
#         # else:
#         #     print("ℹ️ Default admin user already exists.")
#
#     except Exception as e:
#         print(f"❌ Migration or user creation failed: {e}")
#         raise
#     finally:
#         print("--- Restoring original DB config ---")
#         app.config['SQLALCHEMY_DATABASE_URI'] = original_uri
#         if original_binds:
#             app.config['SQLALCHEMY_BINDS'] = original_binds
from flask import current_app
from alembic.config import Config
from alembic import command
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def run_tenant_migrations(db_uri, sub_domain, name):
    app = current_app._get_current_object()

    original_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    original_binds = app.config.get('SQLALCHEMY_BINDS')

    migrations_dir = os.path.join(app.root_path, 'migrations')
    alembic_ini_path = os.path.join(migrations_dir, 'alembic.ini')

    if not os.path.exists(migrations_dir):
        raise Exception("Migrations directory not found. Run 'flask db init' first.")
    if not os.path.exists(alembic_ini_path):
        raise Exception(f"alembic.ini not found at {alembic_ini_path}")

    try:
        # Override app DB config temporarily
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        app.config.pop('SQLALCHEMY_BINDS', None)

        print(f"Running migrations for tenant DB: {db_uri}")

        alembic_cfg = Config(alembic_ini_path)
        alembic_cfg.set_main_option("script_location", migrations_dir)

        alembic_cfg.set_main_option('sqlalchemy.url', db_uri)

        # Run Alembic upgrade to head on tenant DB
        command.upgrade(alembic_cfg, 'head')
        print("Migrations completed successfully.")

        # Now do your default user insertion logic here...

    except Exception as e:
        print(f"Migration or user creation failed: {e}")
        raise
    finally:
        print("Restoring original DB config")
        app.config['SQLALCHEMY_DATABASE_URI'] = original_uri
        if original_binds:
            app.config['SQLALCHEMY_BINDS'] = original_binds
