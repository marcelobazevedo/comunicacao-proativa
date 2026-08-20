"""Registra a impressão digital de cada verificação meteorológica."""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "verificacoes_meteorologicas",
        sa.Column("identificador", sa.Integer(), primary_key=True),
        sa.Column(
            "execucao_id",
            sa.Integer(),
            sa.ForeignKey("execucoes.identificador"),
            nullable=False,
        ),
        sa.Column("resumo_criptografico", sa.String(64), nullable=False),
        sa.Column("houve_mudanca", sa.Boolean(), nullable=False),
        sa.Column("verificada_em", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_verificacoes_meteorologicas_execucao_id",
        "verificacoes_meteorologicas",
        ["execucao_id"],
    )
    op.create_index(
        "ix_verificacoes_meteorologicas_resumo_criptografico",
        "verificacoes_meteorologicas",
        ["resumo_criptografico"],
    )


def downgrade() -> None:
    op.drop_table("verificacoes_meteorologicas")
