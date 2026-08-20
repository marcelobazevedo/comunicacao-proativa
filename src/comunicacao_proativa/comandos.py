import argparse
import json
import logging

from alembic import command
from alembic.config import Config

from comunicacao_proativa.aplicacao.executor import executar_fluxo
from comunicacao_proativa.aplicacao.monitor import monitorar
from comunicacao_proativa.configuracao import obter_configuracao
from comunicacao_proativa.dominio.contatos import normalizar_telefone
from comunicacao_proativa.infraestrutura.banco_dados import (
    criar_dados_iniciais,
    criar_fabrica_sessoes,
)
from comunicacao_proativa.infraestrutura.evolution_api import ProvedorEvolutionApi
from comunicacao_proativa.infraestrutura.modelos_linguagem import validar_acesso_groq


def principal() -> int:
    analisador = argparse.ArgumentParser(description="Comunicação proativa com segurados")
    analisador.add_argument(
        "acao",
        choices=[
            "preparar",
            "executar",
            "monitorar",
            "validar-groq",
            "validar-evolution",
            "testar-whatsapp",
        ],
    )
    analisador.add_argument("--numero", help="Telefone do teste real, com DDD.")
    analisador.add_argument(
        "--mensagem", default="Teste de integração do Protege Antes com a Evolution API."
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
    elif argumentos.acao == "validar-groq":
        validar_acesso_groq(configuracao)
        print(f"Groq validado; modelo {configuracao.GROQ_MODELO} disponível.")
    elif argumentos.acao == "validar-evolution":
        resultado = ProvedorEvolutionApi(configuracao).diagnosticar()
        print(json.dumps(resultado, ensure_ascii=False))
    else:
        if not argumentos.numero:
            analisador.error("A ação testar-whatsapp exige --numero.")
        resultado = ProvedorEvolutionApi(configuracao).enviar(
            normalizar_telefone(argumentos.numero), argumentos.mensagem
        )
        print(json.dumps(resultado.__dict__, ensure_ascii=False))
    return 0
