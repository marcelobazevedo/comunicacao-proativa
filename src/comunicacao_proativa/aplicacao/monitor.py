"""Processo independente para verificações meteorológicas periódicas."""

import logging
from threading import Event

from comunicacao_proativa.aplicacao.executor import executar_fluxo


def monitorar(configuracao, fabrica_sessoes) -> None:
    if not configuracao.MONITORAMENTO_ATIVO:
        logging.info("Monitoramento automático desativado pelo .env.")
        return
    intervalo_segundos = configuracao.INTERVALO_MONITORAMENTO_MINUTOS * 60
    logging.info(
        "Monitoramento iniciado com intervalo de %s minuto(s).",
        configuracao.INTERVALO_MONITORAMENTO_MINUTOS,
    )
    parada = Event()
    while not parada.is_set():
        try:
            identificador = executar_fluxo(configuracao, fabrica_sessoes, origem="automatica")
            logging.info("Verificação automática #%s concluída.", identificador)
        except Exception:
            logging.exception("Falha na verificação meteorológica automática.")
        parada.wait(intervalo_segundos)
