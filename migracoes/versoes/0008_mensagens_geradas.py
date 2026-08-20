"""Separa mensagens geradas das notificações simuladas."""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mensagens",
        sa.Column("identificador", sa.Integer(), primary_key=True),
        sa.Column(
            "execucao_id",
            sa.Integer(),
            sa.ForeignKey("execucoes.identificador"),
            nullable=False,
        ),
        sa.Column(
            "segurado_id",
            sa.Integer(),
            sa.ForeignKey("segurados.identificador"),
            nullable=False,
        ),
        sa.Column("tipo_evento", sa.String(40), nullable=False),
        sa.Column("conteudo", sa.Text(), nullable=False),
        sa.Column("provedor_modelo", sa.String(80), nullable=False),
        sa.Column("criada_em", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_mensagens_execucao", "mensagens", ["execucao_id"])
    op.create_index("ix_mensagens_segurado", "mensagens", ["segurado_id"])


def downgrade() -> None:
    op.drop_table("mensagens")
