"""Estrutura inicial do banco de dados."""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "segurados",
        sa.Column("identificador", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("cidade", sa.String(120), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
    )
    op.create_index("ix_segurados_cidade", "segurados", ["cidade"])
    op.create_table(
        "execucoes",
        sa.Column("identificador", sa.Integer(), primary_key=True),
        sa.Column("iniciada_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("concluida_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("modo", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("erro", sa.Text(), nullable=True),
    )
    op.create_table(
        "apolices",
        sa.Column("identificador", sa.Integer(), primary_key=True),
        sa.Column(
            "segurado_id", sa.Integer(), sa.ForeignKey("segurados.identificador"), nullable=False
        ),
        sa.Column("tipo", sa.String(30), nullable=False),
    )
    op.create_index("ix_apolices_segurado_id", "apolices", ["segurado_id"])
    op.create_table(
        "eventos_climaticos",
        sa.Column("identificador", sa.Integer(), primary_key=True),
        sa.Column(
            "execucao_id", sa.Integer(), sa.ForeignKey("execucoes.identificador"), nullable=False
        ),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("cidade", sa.String(120), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("severidade", sa.String(20), nullable=False),
        sa.Column("evidencia", sa.Text(), nullable=False),
    )
    op.create_index("ix_eventos_climaticos_execucao_id", "eventos_climaticos", ["execucao_id"])
    op.create_table(
        "notificacoes",
        sa.Column("identificador", sa.Integer(), primary_key=True),
        sa.Column(
            "execucao_id", sa.Integer(), sa.ForeignKey("execucoes.identificador"), nullable=False
        ),
        sa.Column(
            "segurado_id", sa.Integer(), sa.ForeignKey("segurados.identificador"), nullable=False
        ),
        sa.Column("tipo_evento", sa.String(40), nullable=False),
        sa.Column("apolice", sa.String(30), nullable=False),
        sa.Column("mensagem", sa.Text(), nullable=False),
        sa.Column("provedor_modelo", sa.String(80), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("criada_em", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notificacoes_execucao_id", "notificacoes", ["execucao_id"])
    op.create_index("ix_notificacoes_segurado_id", "notificacoes", ["segurado_id"])


def downgrade() -> None:
    op.drop_table("notificacoes")
    op.drop_table("eventos_climaticos")
    op.drop_table("apolices")
    op.drop_table("execucoes")
    op.drop_table("segurados")
