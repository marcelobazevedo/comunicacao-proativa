"""Acrescenta estado e país ao endereço do segurado."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "segurados", sa.Column("estado", sa.String(2), nullable=False, server_default="SP")
    )
    op.add_column("segurados", sa.Column("pais", sa.String(2), nullable=False, server_default="BR"))


def downgrade() -> None:
    op.drop_column("segurados", "pais")
    op.drop_column("segurados", "estado")
