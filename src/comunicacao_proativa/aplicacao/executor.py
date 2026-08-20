from comunicacao_proativa.configuracao import Configuracao
from comunicacao_proativa.infraestrutura.banco_dados import (
    EventoModelo,
    ExecucaoModelo,
    agora_utc,
    listar_segurados,
)
from comunicacao_proativa.infraestrutura.meteorologia import ProvedorOpenMeteo
from comunicacao_proativa.infraestrutura.modelos_linguagem import GeradorDeMensagem

from .estado_fluxo import EstadoFluxo
from .grafo_comunicacao import criar_grafo


def executar_fluxo(configuracao: Configuracao, fabrica_sessoes, origem: str = "manual") -> int:
    if origem not in {"manual", "automatica"}:
        raise ValueError("A origem deve ser 'manual' ou 'automatica'.")
    with fabrica_sessoes.begin() as sessao:
        execucao = ExecucaoModelo(
            iniciada_em=agora_utc(),
            modo=origem,
            status="executando",
        )
        sessao.add(execucao)
        sessao.flush()
        identificador = execucao.identificador

    provedor = ProvedorOpenMeteo(
        fabrica_sessoes=fabrica_sessoes,
        identificador_execucao=identificador,
    )
    grafo = criar_grafo(
        provedor,
        GeradorDeMensagem(configuracao),
        fabrica_sessoes,
        configuracao.obter_parametros_alerta(),
        configuracao.CANAL_NOTIFICACAO,
    )
    estado_inicial: EstadoFluxo = {
        "identificador_execucao": identificador,
        "origem": origem,
        "segurados": listar_segurados(fabrica_sessoes),
        "previsoes": [],
        "eventos": [],
        "destinatarios": [],
        "mensagens": [],
        "erros": [],
        "houve_mudanca": False,
    }
    try:
        resultado = grafo.invoke(estado_inicial)
        with fabrica_sessoes.begin() as sessao:
            vistos = set()
            for _, evento in resultado["eventos"]:
                chave = (evento.tipo, evento.cidade, evento.data)
                if chave in vistos:
                    continue
                vistos.add(chave)
                sessao.add(
                    EventoModelo(
                        execucao_id=identificador,
                        tipo=evento.tipo.value,
                        cidade=evento.cidade,
                        data=evento.data,
                        severidade=evento.severidade,
                        evidencia=evento.evidencia,
                    )
                )
            execucao = sessao.get(ExecucaoModelo, identificador)
            if resultado["erros"] and not resultado["previsoes"]:
                execucao.status = "erro"
            elif resultado["erros"]:
                execucao.status = "concluida_com_ressalvas"
            else:
                execucao.status = "concluida"
            execucao.concluida_em = agora_utc()
            execucao.erro = "\n".join(resultado["erros"]) or None
    except Exception as erro:
        with fabrica_sessoes.begin() as sessao:
            execucao = sessao.get(ExecucaoModelo, identificador)
            execucao.status = "erro"
            execucao.concluida_em = agora_utc()
            execucao.erro = str(erro)
        raise
    return identificador
