"""drop_contacts_customer_id

Revision ID: e4940deabe90
Revises: c1d2e3f4a5b6
Create Date: 2025-12-25 06:43:58.229724

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "e4940deabe90"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "contacts" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("contacts")}
        indexes = {index["name"] for index in inspector.get_indexes("contacts")}

        if "stage" in columns:
            op.execute(sa.text("UPDATE contacts SET stage = 'account' WHERE stage = 'customer'"))

        if "customer_id" in columns:
            if "ix_contacts_customer_id" in indexes:
                op.drop_index("ix_contacts_customer_id", table_name="contacts")

            with op.batch_alter_table("contacts") as batch_op:
                batch_op.drop_column("customer_id")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "contacts" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("contacts")}

        if "customer_id" not in columns:
            with op.batch_alter_table("contacts") as batch_op:
                batch_op.add_column(
                    sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True)
                )
                batch_op.create_index("ix_contacts_customer_id", ["customer_id"])

        if "stage" in columns:
            op.execute(sa.text("UPDATE contacts SET stage = 'customer' WHERE stage = 'account'"))
