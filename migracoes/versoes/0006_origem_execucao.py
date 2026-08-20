"""Normaliza o modo como origem manual ou automática."""

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE execucoes SET modo = 'manual' WHERE modo IN ('real', 'demonstracao')")


def downgrade() -> None:
    op.execute("UPDATE execucoes SET modo = 'real' WHERE modo = 'manual'")
