"""change_user_constraints_to_per_tenant_uniqueness

Revision ID: 1275a5851a69
Revises: 8aabad7a20d7
Create Date: 2025-10-03 13:45:29.707771

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1275a5851a69"
down_revision = "8aabad7a20d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Replace global unique constraints on username and email with per-tenant constraints.
    This allows the same username/email to exist in different tenants.
    """
    # Drop existing global unique constraints
    op.drop_constraint("users_username_key", "users", type_="unique")
    op.drop_constraint("users_email_key", "users", type_="unique")

    # Create new composite unique constraints (tenant_id + username/email)
    op.create_unique_constraint("uq_users_tenant_username", "users", ["tenant_id", "username"])
    op.create_unique_constraint("uq_users_tenant_email", "users", ["tenant_id", "email"])


def downgrade() -> None:
    """
    Revert to global unique constraints.
    WARNING: This will fail if duplicate usernames/emails exist across tenants.
    """
    # Drop per-tenant constraints
    op.drop_constraint("uq_users_tenant_username", "users", type_="unique")
    op.drop_constraint("uq_users_tenant_email", "users", type_="unique")

    # Recreate global unique constraints
    op.create_unique_constraint("users_username_key", "users", ["username"])
    op.create_unique_constraint("users_email_key", "users", ["email"])
