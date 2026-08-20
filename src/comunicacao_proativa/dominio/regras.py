from dataclasses import dataclass

from .entidades import EventoClimatico, Previsao, Segurado, TipoApolice, TipoEvento


@dataclass(frozen=True)
class ParametrosAlerta:
    chuva_intensa_mm: float
    chuva_com_probabilidade_mm: float
    probabilidade_minima_chuva: int
    vento_forte_kmh: float
    vento_severidade_alta_kmh: float
    codigos_wmo_granizo: frozenset[int]


def detectar_eventos(previsao: Previsao, parametros: ParametrosAlerta) -> list[EventoClimatico]:
    eventos: list[EventoClimatico] = []
    if previsao.precipitacao_mm >= parametros.chuva_intensa_mm or (
        previsao.precipitacao_mm >= parametros.chuva_com_probabilidade_mm
        and previsao.probabilidade_precipitacao >= parametros.probabilidade_minima_chuva
    ):
        severidade = (
            "alta" if previsao.precipitacao_mm >= parametros.chuva_intensa_mm else "moderada"
        )
        eventos.append(
            EventoClimatico(
                TipoEvento.CHUVA_INTENSA,
                previsao.cidade,
                previsao.data,
                severidade,
                f"{previsao.precipitacao_mm:.0f} mm e probabilidade de "
                f"{previsao.probabilidade_precipitacao}%",
            )
        )
    if previsao.rajada_vento_kmh >= parametros.vento_forte_kmh:
        severidade = (
            "alta"
            if previsao.rajada_vento_kmh >= parametros.vento_severidade_alta_kmh
            else "moderada"
        )
        eventos.append(
            EventoClimatico(
                TipoEvento.VENTO_FORTE,
                previsao.cidade,
                previsao.data,
                severidade,
                f"rajadas de até {previsao.rajada_vento_kmh:.0f} km/h",
            )
        )
    if previsao.codigo_meteorologico in parametros.codigos_wmo_granizo:
        eventos.append(
            EventoClimatico(
                TipoEvento.GRANIZO,
                previsao.cidade,
                previsao.data,
                "alta",
                "previsão de trovoada com granizo (código WMO)",
            )
        )
    return eventos


RELEVANCIA = {
    TipoEvento.CHUVA_INTENSA: {TipoApolice.RESIDENCIAL, TipoApolice.AUTOMOVEL},
    TipoEvento.VENTO_FORTE: {TipoApolice.RESIDENCIAL, TipoApolice.AUTOMOVEL},
    TipoEvento.GRANIZO: {TipoApolice.AUTOMOVEL},
}


def escolher_apolice(segurado: Segurado, evento: EventoClimatico) -> TipoApolice | None:
    return next((item for item in segurado.apolices if item in RELEVANCIA[evento.tipo]), None)
