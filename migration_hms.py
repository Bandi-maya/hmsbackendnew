import logging
from logging.config import fileConfig
from flask import current_app
from sqlalchemy import engine_from_config, pool
from alembic import context

from app import create_app
from extentions import db  # your SQLAlchemy instance

# Alembic Config object
config = context.config
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

target_metadata = db.metadata

def get_url():
    """Get SQLALCHEMY_DATABASE_URI from Flask app."""
    return current_app.config.get("SQLALCHEMY_DATABASE_URI")

def run_migrations_offline():
    """Run migrations in offline mode."""
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in online mode."""
    app = create_app()
    with app.app_context():  # <-- ensures current_app works
        connectable = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            url=get_url()  # <-- critical fix
        )

        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,  # detects column type changes (e.g., VARCHAR size)
            )

            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
