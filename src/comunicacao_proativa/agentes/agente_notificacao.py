from comunicacao_proativa.aplicacao.estado_fluxo import EstadoFluxo
from comunicacao_proativa.infraestrutura.banco_dados import NotificacaoModelo, agora_utc


class AgenteNotificacao:
    def __init__(self, fabrica_sessoes, canal: str) -> None:
        self.fabrica_sessoes = fabrica_sessoes
        self.canal = canal

    def executar(self, estado: EstadoFluxo) -> dict:
        with self.fabrica_sessoes.begin() as sessao:
            for item in estado["mensagens"]:
                canal = item.destinatario.segurado.canal_preferido or self.canal
                destino = (
                    item.destinatario.segurado.email
                    if canal == "email"
                    else item.destinatario.segurado.telefone
                )
                sessao.add(
                    NotificacaoModelo(
                        execucao_id=estado["identificador_execucao"],
                        segurado_id=item.destinatario.segurado.identificador,
                        tipo_evento=item.destinatario.evento.tipo.value,
                        apolice=item.destinatario.apolice.value,
                        mensagem=item.conteudo,
                        provedor_modelo=item.provedor_modelo,
                        status="simulada",
                        canal=canal,
                        destino=destino,
                        criada_em=agora_utc(),
                    )
                )
        return {}
