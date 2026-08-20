"""Acrescenta canal à notificação simulada."""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "notificacoes",
        sa.Column("canal", sa.String(20), nullable=False, server_default="push"),
    )


def downgrade() -> None:
    op.drop_column("notificacoes", "canal")
