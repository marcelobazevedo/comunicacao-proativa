from langgraph.graph import END, START, StateGraph

from comunicacao_proativa.agentes.agente_analise_risco import AgenteAnaliseRisco
from comunicacao_proativa.agentes.agente_coleta import AgenteColeta
from comunicacao_proativa.agentes.agente_comunicacao import AgenteComunicacao
from comunicacao_proativa.agentes.agente_decisao import AgenteDecisao
from comunicacao_proativa.agentes.agente_notificacao import AgenteNotificacao
from comunicacao_proativa.agentes.agente_processamento import AgenteProcessamento
from comunicacao_proativa.agentes.agente_verificacao_mudanca import AgenteVerificacaoMudanca

from .auditoria import NoAuditado
from .estado_fluxo import EstadoFluxo


def _decidir_comunicacao(estado: EstadoFluxo) -> str:
    return "comunicar" if estado["destinatarios"] else "encerrar"


def _decidir_processamento(estado: EstadoFluxo) -> str:
    if estado["origem"] == "manual":
        return "processar"
    return "processar" if estado["houve_mudanca"] else "encerrar"


def criar_grafo(
    provedor_meteorologico,
    gerador_mensagem,
    fabrica_sessoes,
    parametros_alerta,
    canal_notificacao,
    provedor_whatsapp=None,
):
    construtor = StateGraph(EstadoFluxo)
    nos = {
        "coletar": AgenteColeta(provedor_meteorologico).executar,
        "verificar_mudanca": AgenteVerificacaoMudanca(fabrica_sessoes).executar,
        "processar": AgenteProcessamento().executar,
        "analisar_risco": AgenteAnaliseRisco(parametros_alerta).executar,
        "decidir": AgenteDecisao(fabrica_sessoes).executar,
        "comunicar": AgenteComunicacao(gerador_mensagem, fabrica_sessoes).executar,
        "notificar": AgenteNotificacao(
            fabrica_sessoes, canal_notificacao, provedor_whatsapp
        ).executar,
    }
    for nome, executar in nos.items():
        construtor.add_node(nome, NoAuditado(nome, executar, fabrica_sessoes))
    construtor.add_edge(START, "coletar")
    construtor.add_edge("coletar", "verificar_mudanca")
    construtor.add_conditional_edges(
        "verificar_mudanca",
        _decidir_processamento,
        {"processar": "processar", "encerrar": END},
    )
    construtor.add_edge("processar", "analisar_risco")
    construtor.add_edge("analisar_risco", "decidir")
    construtor.add_conditional_edges(
        "decidir", _decidir_comunicacao, {"comunicar": "comunicar", "encerrar": END}
    )
    construtor.add_edge("comunicar", "notificar")
    construtor.add_edge("notificar", END)
    return construtor.compile()
