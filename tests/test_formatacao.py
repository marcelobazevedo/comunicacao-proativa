from datetime import UTC, datetime

from comunicacao_proativa.interface_web.formatacao import formatar_data_hora_brasilia


def test_converte_utc_para_brasilia():
    assert formatar_data_hora_brasilia(datetime(2026, 8, 19, 23, 5, tzinfo=UTC)) == (
        "19/08/2026 20:05"
    )
