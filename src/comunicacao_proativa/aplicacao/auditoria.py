import json
from collections.abc import Callable, Mapping
from time import perf_counter

from comunicacao_proativa.aplicacao.estado_fluxo import EstadoFluxo
from comunicacao_proativa.infraestrutura.banco_dados import AuditoriaAgenteModelo, agora_utc


def resumir_estado(estado: Mapping[str, object]) -> str:
    resumo = {}
    for chave, valor in estado.items():
        if isinstance(valor, list):
            resumo[chave] = len(valor)
        elif isinstance(valor, (str, int, float, bool)) or valor is None:
            resumo[chave] = valor
    return json.dumps(resumo, ensure_ascii=False, sort_keys=True)


class NoAuditado:
    def __init__(
        self,
        nome: str,
        executar: Callable[[EstadoFluxo], dict],
        fabrica_sessoes,
    ) -> None:
        self.nome = nome
        self.executar = executar
        self.fabrica_sessoes = fabrica_sessoes

    def __call__(self, state: EstadoFluxo) -> dict:
        estado = state
        inicio = agora_utc()
        cronometro = perf_counter()
        saida = None
        erro_texto = None
        status = "concluido"
        try:
            saida = self.executar(estado)
            return saida
        except Exception as erro:
            status = "erro"
            erro_texto = str(erro)
            raise
        finally:
            fim = agora_utc()
            with self.fabrica_sessoes.begin() as sessao:
                sessao.add(
                    AuditoriaAgenteModelo(
                        execucao_id=estado["identificador_execucao"],
                        agente=self.nome,
                        iniciada_em=inicio,
                        concluida_em=fim,
                        duracao_ms=round((perf_counter() - cronometro) * 1000),
                        entrada_resumo=resumir_estado(estado),
                        saida_resumo=resumir_estado(saida or {}),
                        status=status,
                        erro=erro_texto,
                    )
                )
