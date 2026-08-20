import argparse
import logging

from alembic import command
from alembic.config import Config

from comunicacao_proativa.aplicacao.executor import executar_fluxo
from comunicacao_proativa.aplicacao.monitor import monitorar
from comunicacao_proativa.configuracao import obter_configuracao
from comunicacao_proativa.infraestrutura.banco_dados import (
    criar_dados_iniciais,
    criar_fabrica_sessoes,
)
from comunicacao_proativa.infraestrutura.modelos_linguagem import validar_acesso_groq


def principal() -> int:
    analisador = argparse.ArgumentParser(description="Comunicação proativa com segurados")
    analisador.add_argument(
        "acao", choices=["preparar", "executar", "monitorar", "validar-groq"]
    )
    argumentos = analisador.parse_args()
    configuracao = obter_configuracao()
    fabrica = criar_fabrica_sessoes(configuracao)
    if argumentos.acao == "preparar":
        command.upgrade(Config("alembic.ini"), "head")
        criar_dados_iniciais(fabrica)
        print("Banco preparado e dados fictícios carregados.")
    elif argumentos.acao == "executar":
        identificador = executar_fluxo(configuracao, fabrica, origem="manual")
        print(f"Execução #{identificador} finalizada.")
    elif argumentos.acao == "monitorar":
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
        monitorar(configuracao, fabrica)
    else:
        validar_acesso_groq(configuracao)
        print(f"Groq validado; modelo {configuracao.GROQ_MODELO} disponível.")
    return 0
