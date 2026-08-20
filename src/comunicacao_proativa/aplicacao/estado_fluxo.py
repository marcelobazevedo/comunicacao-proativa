from typing import TypedDict

from comunicacao_proativa.dominio.entidades import (
    Destinatario,
    EventoClimatico,
    MensagemGerada,
    Previsao,
    Segurado,
)


class EstadoFluxo(TypedDict):
    identificador_execucao: int
    origem: str
    segurados: list[Segurado]
    previsoes: list[tuple[Segurado, Previsao]]
    eventos: list[tuple[Segurado, EventoClimatico]]
    destinatarios: list[Destinatario]
    mensagens: list[MensagemGerada]
    erros: list[str]
    houve_mudanca: bool
