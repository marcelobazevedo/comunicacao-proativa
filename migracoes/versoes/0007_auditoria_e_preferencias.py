"""Acrescenta preferências, consultas, decisões e auditoria dos agentes."""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "segurados",
        sa.Column("canal_preferido", sa.String(20), nullable=False, server_default="push"),
    )
    op.create_table(
        "consultas_meteorologicas",
        sa.Column("identificador", sa.Integer(), primary_key=True),
        sa.Column(
            "execucao_id", sa.Integer(), sa.ForeignKey("execucoes.identificador"), nullable=False
        ),
        sa.Column(
            "segurado_id", sa.Integer(), sa.ForeignKey("segurados.identificador"), nullable=False
        ),
        sa.Column("fonte", sa.String(80), nullable=False),
        sa.Column("parametros", sa.Text(), nullable=False),
        sa.Column("resposta", sa.Text(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("tentativa", sa.Integer(), nullable=False),
        sa.Column("duracao_ms", sa.Integer(), nullable=False),
        sa.Column("erro", sa.Text(), nullable=True),
        sa.Column("consultada_em", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_consultas_execucao", "consultas_meteorologicas", ["execucao_id"])
    op.create_index("ix_consultas_segurado", "consultas_meteorologicas", ["segurado_id"])
    op.create_table(
        "decisoes",
        sa.Column("identificador", sa.Integer(), primary_key=True),
        sa.Column(
            "execucao_id", sa.Integer(), sa.ForeignKey("execucoes.identificador"), nullable=False
        ),
        sa.Column(
            "segurado_id", sa.Integer(), sa.ForeignKey("segurados.identificador"), nullable=False
        ),
        sa.Column("tipo_evento", sa.String(40), nullable=True),
        sa.Column("elegivel", sa.Boolean(), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("decidida_em", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_decisoes_execucao", "decisoes", ["execucao_id"])
    op.create_index("ix_decisoes_segurado", "decisoes", ["segurado_id"])
    op.create_table(
        "auditorias_agentes",
        sa.Column("identificador", sa.Integer(), primary_key=True),
        sa.Column(
            "execucao_id", sa.Integer(), sa.ForeignKey("execucoes.identificador"), nullable=False
        ),
        sa.Column("agente", sa.String(60), nullable=False),
        sa.Column("iniciada_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("concluida_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duracao_ms", sa.Integer(), nullable=False),
        sa.Column("entrada_resumo", sa.Text(), nullable=False),
        sa.Column("saida_resumo", sa.Text(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("erro", sa.Text(), nullable=True),
    )
    op.create_index("ix_auditorias_execucao", "auditorias_agentes", ["execucao_id"])


def downgrade() -> None:
    op.drop_table("auditorias_agentes")
    op.drop_table("decisoes")
    op.drop_table("consultas_meteorologicas")
    op.drop_column("segurados", "canal_preferido")
