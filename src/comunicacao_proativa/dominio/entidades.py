from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class TipoApolice(StrEnum):
    RESIDENCIAL = "residencial"
    AUTOMOVEL = "automovel"


class TipoEvento(StrEnum):
    CHUVA_INTENSA = "chuva_intensa"
    VENTO_FORTE = "vento_forte"
    GRANIZO = "granizo"


@dataclass(frozen=True)
class Segurado:
    identificador: int
    nome: str
    cidade: str
    estado: str
    pais: str
    latitude: float
    longitude: float
    apolices: tuple[TipoApolice, ...]
    canal_preferido: str = "push"


@dataclass(frozen=True)
class Previsao:
    cidade: str
    data: date
    codigo_meteorologico: int
    precipitacao_mm: float
    probabilidade_precipitacao: int
    rajada_vento_kmh: float


@dataclass(frozen=True)
class EventoClimatico:
    tipo: TipoEvento
    cidade: str
    data: date
    severidade: str
    evidencia: str


@dataclass(frozen=True)
class Destinatario:
    segurado: Segurado
    evento: EventoClimatico
    apolice: TipoApolice


@dataclass(frozen=True)
class MensagemGerada:
    destinatario: Destinatario
    conteudo: str
    provedor_modelo: str
