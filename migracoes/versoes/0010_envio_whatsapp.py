"""Acrescenta rastreabilidade para envio real por WhatsApp."""

import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("notificacoes") as lote:
        lote.add_column(sa.Column("identificador_externo", sa.String(160), nullable=True))
        lote.add_column(sa.Column("instancia", sa.String(120), nullable=True))
        lote.add_column(sa.Column("tentativas", sa.Integer(), nullable=False, server_default="0"))
        lote.add_column(sa.Column("ultima_tentativa_em", sa.DateTime(timezone=True), nullable=True))
        lote.add_column(sa.Column("confirmada_em", sa.DateTime(timezone=True), nullable=True))
        lote.add_column(sa.Column("codigo_http", sa.Integer(), nullable=True))
        lote.add_column(sa.Column("resposta_resumo", sa.Text(), nullable=True))
        lote.add_column(sa.Column("erro_envio", sa.Text(), nullable=True))
        lote.add_column(sa.Column("chave_idempotencia", sa.String(64), nullable=True))

    conexao = op.get_bind()
    registros = conexao.execute(sa.text("SELECT identificador FROM notificacoes")).scalars()
    for identificador in registros:
        conexao.execute(
            sa.text(
                "UPDATE notificacoes SET chave_idempotencia = :chave "
                "WHERE identificador = :identificador"
            ),
            {"chave": f"legado-{identificador:056d}", "identificador": identificador},
        )

    with op.batch_alter_table("notificacoes") as lote:
        lote.alter_column(
            "chave_idempotencia", existing_type=sa.String(64), nullable=False
        )
        lote.create_index("ix_notificacoes_chave_idempotencia", ["chave_idempotencia"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("notificacoes") as lote:
        lote.drop_index("ix_notificacoes_chave_idempotencia")
        lote.drop_column("chave_idempotencia")
        lote.drop_column("erro_envio")
        lote.drop_column("resposta_resumo")
        lote.drop_column("codigo_http")
        lote.drop_column("confirmada_em")
        lote.drop_column("ultima_tentativa_em")
        lote.drop_column("tentativas")
        lote.drop_column("instancia")
        lote.drop_column("identificador_externo")
