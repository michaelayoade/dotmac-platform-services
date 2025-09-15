"""
Initial baseline migration

This creates an empty baseline so that Alembic can stamp the database and
subsequent migrations can be applied safely via the migration job.
"""


# revision identifiers, used by Alembic.
revision = "0001_initial_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Baseline has no schema changes."""
    # Intentionally empty – establishes Alembic versioning
    pass


def downgrade() -> None:
    """Baseline rollback does nothing."""
    # Intentionally empty
    pass

