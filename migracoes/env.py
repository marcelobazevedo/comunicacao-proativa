from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from comunicacao_proativa.configuracao import obter_configuracao
from comunicacao_proativa.infraestrutura.banco_dados import Base

configuracao_alembic = context.config
if configuracao_alembic.config_file_name:
    fileConfig(configuracao_alembic.config_file_name)
configuracao_alembic.set_main_option("sqlalchemy.url", obter_configuracao().BANCO_URL)
metadados_alvo = Base.metadata


def executar_migracoes_desconectadas() -> None:
    context.configure(
        url=configuracao_alembic.get_main_option("sqlalchemy.url"),
        target_metadata=metadados_alvo,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def executar_migracoes_conectadas() -> None:
    motor = engine_from_config(
        configuracao_alembic.get_section(configuracao_alembic.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with motor.connect() as conexao:
        context.configure(connection=conexao, target_metadata=metadados_alvo)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    executar_migracoes_desconectadas()
else:
    executar_migracoes_conectadas()
