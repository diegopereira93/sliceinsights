from logging.config import fileConfig
import os
import sys
from sqlmodel import SQLModel
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Add the project root to sys.path to allow imports
sys.path.append(os.getcwd())

# Import your models here to register them with SQLModel
from app.models import paddle, brand, market_offer  # noqa

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section, {})
    # Override sqlalchemy.url with environment variable if present
    db_url = os.getenv("DATABASE_URL_SYNC")
    if db_url:
        configuration["sqlalchemy.url"] = db_url
    
    # Debug print
    print(f"DEBUG: Using database URL: {configuration.get('sqlalchemy.url')}")

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
