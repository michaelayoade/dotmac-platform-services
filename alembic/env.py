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

# =============================================================================
# Import all models to ensure they're registered with Base.metadata
# This ensures alembic autogenerate can detect all tables
# =============================================================================

# Core database
from dotmac.platform.db import Base  # noqa: E402

# Auth and user management
from dotmac.platform.auth.models import *  # noqa: F401,F403,E402

# Core and base models
from dotmac.platform.core.models import *  # noqa: F401,F403,E402

try:
    from dotmac.platform.user_management.models import *  # noqa: F401,F403,E402
except ImportError:
    pass

# Billing
from dotmac.platform.billing.bank_accounts.entities import *  # noqa: F401,F403,E402
from dotmac.platform.billing.bank_accounts.models import *  # noqa: F401,F403,E402
from dotmac.platform.billing.catalog.models import *  # noqa: F401,F403,E402
from dotmac.platform.billing.core.entities import *  # noqa: F401,F403,E402
from dotmac.platform.billing.core.models import *  # noqa: F401,F403,E402
from dotmac.platform.billing.pricing.models import *  # noqa: F401,F403,E402
from dotmac.platform.billing.receipts.models import *  # noqa: F401,F403,E402
from dotmac.platform.billing.settings.models import *  # noqa: F401,F403,E402
from dotmac.platform.billing.subscriptions.models import *  # noqa: F401,F403,E402

try:
    from dotmac.platform.billing.addons.models import *  # noqa: F401,F403,E402
except ImportError:
    pass

try:
    from dotmac.platform.billing.currency.models import *  # noqa: F401,F403,E402
except ImportError:
    pass

try:
    from dotmac.platform.billing.dunning.models import *  # noqa: F401,F403,E402
except ImportError:
    pass

try:
    from dotmac.platform.billing.payment_methods.models import *  # noqa: F401,F403,E402
except ImportError:
    pass

try:
    from dotmac.platform.billing.usage.models import *  # noqa: F401,F403,E402
except ImportError:
    pass

# Customer and contacts
from dotmac.platform.contacts.models import *  # noqa: F401,F403,E402
from dotmac.platform.customer_management.models import *  # noqa: F401,F403,E402
from dotmac.platform.partner_management.models import *  # noqa: F401,F403,E402

# Analytics and audit
from dotmac.platform.analytics.models import *  # noqa: F401,F403,E402
from dotmac.platform.audit.models import *  # noqa: F401,F403,E402

# Communications and webhooks
from dotmac.platform.communications.models import *  # noqa: F401,F403,E402
from dotmac.platform.webhooks.models import *  # noqa: F401,F403,E402

# Data operations
from dotmac.platform.data_transfer.models import *  # noqa: F401,F403,E402

try:
    from dotmac.platform.data_import.models import *  # noqa: F401,F403,E402
except ImportError:
    pass

# Admin settings
try:
    from dotmac.platform.admin.settings.models import *  # noqa: F401,F403,E402
except ImportError:
    pass

# Ticketing
try:
    from dotmac.platform.ticketing.models import *  # noqa: F401,F403,E402
except ImportError:
    pass

# Licensing Framework
try:
    from dotmac.platform.licensing.framework import *  # noqa: F401,F403,E402
except ImportError:
    pass

try:
    from dotmac.platform.licensing.models import *  # noqa: F401,F403,E402
except ImportError:
    pass

# Orchestration and Workflows
try:
    from dotmac.platform.orchestration.models import *  # noqa: F401,F403,E402
except ImportError:
    pass

try:
    from dotmac.platform.workflows.models import *  # noqa: F401,F403,E402
except ImportError:
    pass

# Monitoring
try:
    from dotmac.platform.monitoring.models import *  # noqa: F401,F403,E402
except ImportError:
    pass

try:
    from dotmac.platform.fault_management.models import *  # noqa: F401,F403,E402
except ImportError:
    pass

# Jobs
try:
    from dotmac.platform.jobs.models import *  # noqa: F401,F403,E402
except ImportError:
    pass

# CRM
try:
    from dotmac.platform.crm.models import *  # noqa: F401,F403,E402
except ImportError:
    pass

# Notifications
try:
    from dotmac.platform.notifications.models import *  # noqa: F401,F403,E402
except ImportError:
    pass

# AI
try:
    from dotmac.platform.ai.models import *  # noqa: F401,F403,E402
except ImportError:
    pass

# Tenant
try:
    from dotmac.platform.tenant.models import *  # noqa: F401,F403,E402
except ImportError:
    pass

# Use Base.metadata for autogeneration
target_metadata = Base.metadata


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

        # Run migrations - the connection already has a transaction started
        with context.begin_transaction():
            context.run_migrations()

        # Explicitly commit the transaction to ensure changes persist
        connection.commit()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
