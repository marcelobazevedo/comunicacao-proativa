from datetime import date
from typing import cast

from sqlalchemy import func, select

from comunicacao_proativa.agentes.agente_notificacao import AgenteNotificacao
from comunicacao_proativa.aplicacao.estado_fluxo import EstadoFluxo
from comunicacao_proativa.aplicacao.grafo_comunicacao import (
    _decidir_processamento,
    criar_grafo,
)
from comunicacao_proativa.dominio.entidades import Previsao
from comunicacao_proativa.infraestrutura.banco_dados import (
    AuditoriaAgenteModelo,
    DecisaoModelo,
    ExecucaoModelo,
    NotificacaoModelo,
    agora_utc,
    listar_segurados,
)
from comunicacao_proativa.infraestrutura.evolution_api import ResultadoEnvioWhatsapp


class ProvedorFalso:
    def coletar(self, segurado, dias=3):
        return [Previsao(segurado.cidade, date.today(), 96, 62, 95, 92)]


class GeradorFalso:
    nome_provedor = "teste:modelo"

    def gerar(self, destinatario):
        return f"Alerta preventivo para {destinatario.segurado.nome}"


class ProvedorWhatsappFalso:
    instancia = "teste"
    envio_real = True

    def enviar(self, numero, mensagem):
        return ResultadoEnvioWhatsapp("mensagem-123", 1, 201, '{"status":"enviada"}', True)

    def diagnosticar(self):
        return {"estado": "open"}


def test_execucao_manual_processa_sem_mudanca_e_automatica_nao():
    manual = cast(EstadoFluxo, {"origem": "manual", "houve_mudanca": False})
    automatica_sem_mudanca = cast(
        EstadoFluxo,
        {"origem": "automatica", "houve_mudanca": False},
    )
    automatica_com_mudanca = cast(
        EstadoFluxo,
        {"origem": "automatica", "houve_mudanca": True},
    )

    assert _decidir_processamento(manual) == "processar"
    assert _decidir_processamento(automatica_sem_mudanca) == "encerrar"
    assert _decidir_processamento(automatica_com_mudanca) == "processar"


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
        "whatsapp",
        ProvedorWhatsappFalso(),
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
    agente_notificacao = AgenteNotificacao(
        fabrica_sessoes,
        "whatsapp",
        ProvedorWhatsappFalso(),
    )
    agente_notificacao.executar(resultado)
    with fabrica_sessoes() as sessao:
        assert sessao.scalar(select(func.count()).select_from(AuditoriaAgenteModelo)) == 7
        assert sessao.scalar(select(func.count()).select_from(DecisaoModelo)) > 0
        assert sessao.scalar(select(func.count()).select_from(NotificacaoModelo)) > 0
        notificacao = sessao.scalar(select(NotificacaoModelo).limit(1))
        assert notificacao.canal == "whatsapp"
        assert notificacao.destino.startswith("55")
        assert notificacao.status == "enviada"
        assert notificacao.identificador_externo == "mensagem-123"
        assert (
            sessao.scalar(select(func.count()).select_from(NotificacaoModelo))
            == len(resultado["mensagens"])
        )
