import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# Add source roots to import path so we can import models from repo layout
project_root = Path(__file__).resolve().parent.parent
src_root = project_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

# Also include each package's src directory (packages/*/src) for namespace packages like `dotmac.*`
packages_dir = project_root / "packages"
if packages_dir.is_dir():
    for pkg in packages_dir.iterdir():
        pkg_src = pkg / "src"
        if pkg_src.is_dir():
            p = str(pkg_src)
            if p not in sys.path:
                sys.path.insert(0, p)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Auth and user management
from dotmac.platform.auth.models import *

# Core and base models
from dotmac.platform.core.models import *
from dotmac.platform.db import Base

# Import all models to ensure they're registered with Base.metadata
# This ensures alembic autogenerate can detect all tables


try:
    from dotmac.platform.user_management.models import *
except ImportError:
    pass  # Skip if circular import issues

from dotmac.platform.billing.bank_accounts.entities import *
from dotmac.platform.billing.bank_accounts.models import *
from dotmac.platform.billing.catalog.models import *
from dotmac.platform.billing.core.entities import *

# Billing (comprehensive)
from dotmac.platform.billing.core.models import *
from dotmac.platform.billing.pricing.models import *
from dotmac.platform.billing.receipts.models import *
from dotmac.platform.billing.settings.models import *
from dotmac.platform.billing.subscriptions.models import *
from dotmac.platform.contacts.models import *

# Customer and contacts
from dotmac.platform.customer_management.models import *
from dotmac.platform.partner_management.models import *

try:
    from dotmac.platform.billing.money_models import *
except ImportError:
    pass

# Analytics and audit
from dotmac.platform.analytics.models import *
from dotmac.platform.audit.models import *

# Communications and webhooks
from dotmac.platform.communications.models import *

# Data operations
from dotmac.platform.data_transfer.models import *
from dotmac.platform.webhooks.models import *

try:
    from dotmac.platform.data_import.models import *
except ImportError:
    pass

# Admin and services
try:
    from dotmac.platform.admin.settings.models import *
except ImportError:
    pass
try:
    from dotmac.platform.service_registry.models import *
except ImportError:
    pass
try:
    from dotmac.platform.ticketing.models import *
except ImportError:
    pass

# Use Base.metadata for autogeneration
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_database_url():
    """Get database URL from environment variable or config."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    # Fallback to config
    return config.get_main_option("sqlalchemy.url")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Override sqlalchemy.url with environment variable if available
    configuration = config.get_section(config.config_ini_section)
    database_url = get_database_url()
    if database_url:
        configuration["sqlalchemy.url"] = database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        try:
            if connection.dialect.name == "postgresql":
                connection.exec_driver_sql("SET lock_timeout = '5s'")
                connection.exec_driver_sql("SET statement_timeout = '60s'")
        except Exception as e:
            print(f"[alembic] Could not set session timeouts: {e}")
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

        # Optionally apply RLS after successful migrations
        try:
            apply_rls = os.getenv("APPLY_RLS_AFTER_MIGRATION", "false").lower() == "true"
            if apply_rls:
                # Try to import and run scripts/setup_rls.apply_rls()
                import asyncio
                from pathlib import Path

                # Ensure project root is on sys.path for 'scripts' import
                project_root = Path(__file__).resolve().parent.parent  # noqa: B008
                if str(project_root) not in sys.path:
                    sys.path.insert(0, str(project_root))
                try:
                    from scripts.setup_rls import apply_rls as _apply_rls

                    print("[alembic] Applying RLS policies after migration...")
                    asyncio.run(_apply_rls())
                    print("[alembic] RLS policies applied.")
                except Exception as e:
                    print(f"[alembic] Skipping RLS setup: {e}")
        except Exception as e:
            print(f"[alembic] Error in RLS post-migration hook: {e}")


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
