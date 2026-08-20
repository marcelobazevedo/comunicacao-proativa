from datetime import date

from sqlalchemy import func, select

from comunicacao_proativa.aplicacao.grafo_comunicacao import criar_grafo
from comunicacao_proativa.dominio.entidades import Previsao
from comunicacao_proativa.infraestrutura.banco_dados import (
    AuditoriaAgenteModelo,
    DecisaoModelo,
    ExecucaoModelo,
    NotificacaoModelo,
    agora_utc,
    listar_segurados,
)


class ProvedorFalso:
    def coletar(self, segurado, dias=3):
        return [Previsao(segurado.cidade, date.today(), 96, 62, 95, 92)]


class GeradorFalso:
    nome_provedor = "teste:modelo"

    def gerar(self, destinatario):
        return f"Alerta preventivo para {destinatario.segurado.nome}"


def test_langgraph_persiste_auditoria_decisoes_e_notificacoes(fabrica_sessoes, configuracao_teste):
    with fabrica_sessoes.begin() as sessao:
        execucao = ExecucaoModelo(iniciada_em=agora_utc(), modo="manual", status="executando")
        sessao.add(execucao)
        sessao.flush()
        identificador = execucao.identificador
    grafo = criar_grafo(
        ProvedorFalso(),
        GeradorFalso(),
        fabrica_sessoes,
        configuracao_teste.obter_parametros_alerta(),
        "push",
    )
    resultado = grafo.invoke(
        {
            "identificador_execucao": identificador,
            "origem": "manual",
            "segurados": listar_segurados(fabrica_sessoes),
            "previsoes": [],
            "eventos": [],
            "destinatarios": [],
            "mensagens": [],
            "erros": [],
            "houve_mudanca": False,
        }
    )
    assert resultado["mensagens"]
    with fabrica_sessoes() as sessao:
        assert sessao.scalar(select(func.count()).select_from(AuditoriaAgenteModelo)) == 7
        assert sessao.scalar(select(func.count()).select_from(DecisaoModelo)) > 0
        assert sessao.scalar(select(func.count()).select_from(NotificacaoModelo)) > 0
        assert sessao.scalar(select(NotificacaoModelo.canal).limit(1)) == "push"
