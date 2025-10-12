import os
from flask import current_app
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

from Models.Department import Department
from Models.UserField import FieldTypeEnum, UserField
from Models.UserType import UserType
from Models.Users import User


def run_tenant_migrations(db_uri, sub_domain, name):
    """
    Runs Alembic migrations for a tenant DB and sets up default data.

    Args:
        db_uri (str): SQLAlchemy URI of the tenant database.
        sub_domain (str): Subdomain for the tenant.
        name (str): Tenant name.
    """
    app = current_app._get_current_object()

    # Store original DB config to restore later
    original_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    original_binds = app.config.get('SQLALCHEMY_BINDS')

    migrations_dir = os.path.join(app.root_path, 'migrations')
    alembic_ini_path = os.path.join(migrations_dir, 'alembic.ini')

    if not os.path.exists(migrations_dir):
        raise Exception("Migrations directory not found. Run 'flask db init' first.")
    if not os.path.exists(alembic_ini_path):
        raise Exception(f"alembic.ini not found at {alembic_ini_path}")

    engine = None
    session = None

    try:
        # Override app DB config temporarily
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        app.config.pop('SQLALCHEMY_BINDS', None)

        print(f"Running migrations for tenant DB: {db_uri}")

        # --- Run Alembic migrations ---
        alembic_cfg = Config(alembic_ini_path)
        alembic_cfg.set_main_option("script_location", migrations_dir)
        alembic_cfg.set_main_option('sqlalchemy.url', db_uri)
        command.upgrade(alembic_cfg, 'head')
        print("✅ Migrations completed successfully.")

        # --- Setup SQLAlchemy engine and session for tenant DB ---
        engine = create_engine(db_uri)
        TenantSession = sessionmaker(bind=engine)
        session = TenantSession()

        # --- Create default User Types ---
        user_types = [
            {"type": "Admin", "description": "Administrator"},
            {"type": "Doctor", "description": "Medical Doctor"},
            {"type": "Patient", "description": "Patient"},
            {"type": "Nurse", "description": "Nursing Staff"},
            {"type": "Receptionist", "description": "Front Desk"},
            {"type": "LabTechnician", "description": "Lab Technician"},
            {"type": "Pharmacist", "description": "Pharmacy Staff"},
        ]

        user_type_map = {}
        for ut in user_types:
            existing = session.query(UserType).filter(UserType.type.ilike(ut["type"])).first()
            if not existing:
                user_type = UserType(type=ut["type"], description=ut["description"])
                user_type.validate_type('type', ut['type'], session=session)
                session.add(user_type)
                session.flush()
                user_type_map[ut["type"]] = user_type.id
            else:
                user_type_map[ut["type"]] = existing.id
        session.commit()
        print("✅ Default user types created.")

        # --- Create default Department ---
        dept_name = "Admin Department"
        department = session.query(Department).filter_by(name=dept_name).first()
        if not department:
            department = Department(name=dept_name, description="Created for admin")
            department.validate_name("name", dept_name, session=session)
            session.add(department)
            session.commit()
        print("✅ Default department created.")

        # --- Create User Fields ---
        fields = [
            {"user_type": user_type_map["Doctor"], "field_name": "first_name", "field_type": FieldTypeEnum.STRING, "is_mandatory": True},
            {"user_type": user_type_map["Doctor"], "field_name": "last_name", "field_type": FieldTypeEnum.STRING, "is_mandatory": True},
            {"user_type": user_type_map["Doctor"], "field_name": "specialization", "field_type": FieldTypeEnum.STRING, "is_mandatory": False},
            {"user_type": user_type_map["Doctor"], "field_name": "experience", "field_type": FieldTypeEnum.STRING, "is_mandatory": False},
            {"user_type": user_type_map["Patient"], "field_name": "first_name", "field_type": FieldTypeEnum.STRING, "is_mandatory": True},
            {"user_type": user_type_map["Patient"], "field_name": "last_name", "field_type": FieldTypeEnum.STRING, "is_mandatory": True},
            {"user_type": user_type_map["Patient"], "field_name": "disease", "field_type": FieldTypeEnum.STRING, "is_mandatory": False},
            {"user_type": user_type_map["Patient"], "field_name": "notes", "field_type": FieldTypeEnum.STRING, "is_mandatory": False},
            {"user_type": user_type_map["Patient"], "field_name": "assigned_to_doctor", "field_type": FieldTypeEnum.STRING, "is_mandatory": False},
            {"user_type": user_type_map["Nurse"], "field_name": "first_name", "field_type": FieldTypeEnum.STRING, "is_mandatory": True},
            {"user_type": user_type_map["Nurse"], "field_name": "last_name", "field_type": FieldTypeEnum.STRING, "is_mandatory": True},
            {"user_type": user_type_map["Receptionist"], "field_name": "first_name", "field_type": FieldTypeEnum.STRING, "is_mandatory": True},
            {"user_type": user_type_map["Receptionist"], "field_name": "last_name", "field_type": FieldTypeEnum.STRING, "is_mandatory": True},
            {"user_type": user_type_map["LabTechnician"], "field_name": "first_name", "field_type": FieldTypeEnum.STRING, "is_mandatory": True},
            {"user_type": user_type_map["LabTechnician"], "field_name": "last_name", "field_type": FieldTypeEnum.STRING, "is_mandatory": True},
            {"user_type": user_type_map["Pharmacist"], "field_name": "first_name", "field_type": FieldTypeEnum.STRING, "is_mandatory": True},
            {"user_type": user_type_map["Pharmacist"], "field_name": "last_name", "field_type": FieldTypeEnum.STRING, "is_mandatory": True},
        ]
        for f in fields:
            existing = session.query(UserField).filter_by(user_type=f["user_type"], field_name=f["field_name"]).first()
            if not existing:
                UserField.tenant_session = session
                session.add(UserField(**f))
        session.commit()
        print("✅ Default user fields created.")

        # --- Create default Admin User ---
        admin_email = f"admin@{sub_domain}.com"
        existing_user = session.query(User).filter_by(email=admin_email).first()
        if not existing_user:
            User.tenant_session = session
            admin_user = User(
                name="Admin",
                username=admin_email,
                phone_no=546789,
                address={"h-no": "17-75/a"},
                age=1,
                email=admin_email,
                password=generate_password_hash("admin123"),
                department_id=department.id,
                user_type_id=user_type_map["Admin"],
                date_of_birth="2000-10-10",
                gender="MALE"
            )
            session.add(admin_user)
            session.commit()
            print("✅ Default admin user created.")
        else:
            print("ℹ️ Default admin user already exists.")

    except Exception as e:
        print(f"❌ Migration or user creation failed: {e}")
        raise
    finally:
        if session:
            session.close()
        if engine:
            engine.dispose()
        print("Restoring original DB config")
        app.config['SQLALCHEMY_DATABASE_URI'] = original_uri
        if original_binds:
            app.config['SQLALCHEMY_BINDS'] = original_binds
