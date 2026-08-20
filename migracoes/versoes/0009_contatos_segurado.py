"""Adiciona contatos do segurado e destino da notificação simulada."""

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("segurados") as lote:
        lote.add_column(sa.Column("email", sa.String(254), nullable=True))
        lote.add_column(sa.Column("telefone", sa.String(13), nullable=True))

    conexao = op.get_bind()
    identificadores = conexao.execute(sa.text("SELECT identificador FROM segurados")).scalars()
    for identificador in identificadores:
        conexao.execute(
            sa.text(
                "UPDATE segurados SET email = :email, telefone = :telefone "
                "WHERE identificador = :identificador"
            ),
            {
                "email": f"segurado{identificador}@exemplo.com",
                "telefone": f"55119{identificador:08d}",
                "identificador": identificador,
            },
        )
    conexao.execute(
        sa.text("UPDATE segurados SET canal_preferido = 'whatsapp' WHERE canal_preferido = 'push'")
    )

    with op.batch_alter_table("segurados") as lote:
        lote.alter_column("email", existing_type=sa.String(254), nullable=False)
        lote.alter_column("telefone", existing_type=sa.String(13), nullable=False)

    with op.batch_alter_table("notificacoes") as lote:
        lote.add_column(sa.Column("destino", sa.String(254), nullable=True))
    conexao.execute(
        sa.text(
            "UPDATE notificacoes SET canal = 'whatsapp' WHERE canal = 'push'"
        )
    )
    conexao.execute(
        sa.text(
            "UPDATE notificacoes SET destino = CASE "
            "WHEN canal = 'email' THEN "
            "(SELECT email FROM segurados WHERE segurados.identificador = "
            "notificacoes.segurado_id) ELSE (SELECT telefone FROM segurados WHERE "
            "segurados.identificador = notificacoes.segurado_id) END"
        )
    )
    with op.batch_alter_table("notificacoes") as lote:
        lote.alter_column("destino", existing_type=sa.String(254), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("notificacoes") as lote:
        lote.drop_column("destino")
    with op.batch_alter_table("segurados") as lote:
        lote.drop_column("telefone")
        lote.drop_column("email")
