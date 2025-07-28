"""
Alembic Environment Configuration
Handles database migrations for AUREN LangGraph system
"""

import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
# Import your models here
try:
    from auren.database.models import Base
    target_metadata = Base.metadata
except ImportError:
    target_metadata = None

# Get database URL from environment
def get_url():
    """Get database URL from environment variables"""
    # Try DATABASE_URL first (common in production)
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    
    # Build from components
    user = os.getenv("DB_USER", "auren_user")
    password = os.getenv("DB_PASSWORD", "auren_secure_2025")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    database = os.getenv("DB_NAME", "auren")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
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
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online() 