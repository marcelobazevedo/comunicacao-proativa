"""Agente responsável pela entrega ou simulação das notificações."""

import hashlib

from sqlalchemy import select

from comunicacao_proativa.aplicacao.estado_fluxo import EstadoFluxo
from comunicacao_proativa.infraestrutura.banco_dados import NotificacaoModelo, agora_utc
from comunicacao_proativa.infraestrutura.evolution_api import (
    FalhaEnvioWhatsapp,
    ProvedorEnvioWhatsapp,
    ProvedorWhatsappSimulado,
)


class AgenteNotificacao:
    def __init__(
        self,
        fabrica_sessoes,
        canal: str,
        provedor_whatsapp: ProvedorEnvioWhatsapp | None = None,
    ) -> None:
        self.fabrica_sessoes = fabrica_sessoes
        self.canal = canal
        self.provedor_whatsapp = provedor_whatsapp or ProvedorWhatsappSimulado()

    @staticmethod
    def _chave_idempotencia(estado: EstadoFluxo, item) -> str:
        conteudo = "|".join(
            [
                str(estado["identificador_execucao"]),
                str(item.destinatario.segurado.identificador),
                item.destinatario.evento.tipo.value,
                item.conteudo,
            ]
        )
        return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()

    def executar(self, estado: EstadoFluxo) -> dict:
        erros = list(estado["erros"])
        for item in estado["mensagens"]:
            segurado = item.destinatario.segurado
            canal = segurado.canal_preferido or self.canal
            destino = segurado.email if canal == "email" else segurado.telefone
            chave = self._chave_idempotencia(estado, item)

            with self.fabrica_sessoes.begin() as sessao:
                existente = sessao.scalar(
                    select(NotificacaoModelo).where(
                        NotificacaoModelo.chave_idempotencia == chave
                    )
                )
                if existente is not None:
                    continue
                envio_real = canal == "whatsapp" and self.provedor_whatsapp.envio_real
                notificacao = NotificacaoModelo(
                    execucao_id=estado["identificador_execucao"],
                    segurado_id=segurado.identificador,
                    tipo_evento=item.destinatario.evento.tipo.value,
                    apolice=item.destinatario.apolice.value,
                    mensagem=item.conteudo,
                    provedor_modelo=item.provedor_modelo,
                    status="pendente" if envio_real else "simulada",
                    canal=canal,
                    destino=destino,
                    criada_em=agora_utc(),
                    instancia=self.provedor_whatsapp.instancia if envio_real else None,
                    chave_idempotencia=chave,
                )
                sessao.add(notificacao)
                sessao.flush()
                identificador = notificacao.identificador

            if canal != "whatsapp" or not self.provedor_whatsapp.envio_real:
                continue

            try:
                resultado = self.provedor_whatsapp.enviar(destino, item.conteudo)
                with self.fabrica_sessoes.begin() as sessao:
                    notificacao = sessao.get(NotificacaoModelo, identificador)
                    notificacao.status = "enviada"
                    notificacao.identificador_externo = resultado.identificador_externo
                    notificacao.tentativas = resultado.tentativas
                    notificacao.ultima_tentativa_em = agora_utc()
                    notificacao.confirmada_em = agora_utc()
                    notificacao.codigo_http = resultado.codigo_http
                    notificacao.resposta_resumo = resultado.resposta_resumo
            except FalhaEnvioWhatsapp as erro:
                with self.fabrica_sessoes.begin() as sessao:
                    notificacao = sessao.get(NotificacaoModelo, identificador)
                    notificacao.status = "falha"
                    notificacao.tentativas = erro.tentativas
                    notificacao.ultima_tentativa_em = agora_utc()
                    notificacao.codigo_http = erro.codigo_http
                    notificacao.erro_envio = str(erro)
                erros.append(f"Falha no WhatsApp de {segurado.nome}: {erro}")
        return {"erros": erros}
