"""Acrescenta exclusão lógica ao segurado."""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "segurados", sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true())
    )


def downgrade() -> None:
    op.drop_column("segurados", "ativo")
