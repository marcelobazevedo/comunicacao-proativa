from datetime import date

from comunicacao_proativa.dominio.entidades import Previsao, Segurado, TipoApolice, TipoEvento
from comunicacao_proativa.dominio.regras import ParametrosAlerta, detectar_eventos, escolher_apolice

PARAMETROS = ParametrosAlerta(50, 30, 80, 75, 90, frozenset({96, 99}))


def test_detecta_os_tres_eventos_e_seleciona_apolice():
    previsao = Previsao("São Paulo", date.today(), 96, 62, 95, 92)
    eventos = detectar_eventos(previsao, PARAMETROS)
    assert {evento.tipo for evento in eventos} == {
        TipoEvento.CHUVA_INTENSA,
        TipoEvento.VENTO_FORTE,
        TipoEvento.GRANIZO,
    }
    segurado = Segurado(
        1,
        "Ana",
        "São Paulo",
        "SP",
        "BR",
        -23.5,
        -46.6,
        (TipoApolice.AUTOMOVEL,),
        "sms",
    )
    assert escolher_apolice(segurado, eventos[-1]) == TipoApolice.AUTOMOVEL


def test_nao_detecta_risco_abaixo_dos_limites():
    previsao = Previsao("São Paulo", date.today(), 1, 0, 5, 20)
    assert detectar_eventos(previsao, PARAMETROS) == []
