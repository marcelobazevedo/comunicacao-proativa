from datetime import UTC, datetime
from zoneinfo import ZoneInfo

FUSO_HORARIO_BRASILIA = ZoneInfo("America/Sao_Paulo")


def formatar_data_hora_brasilia(valor: datetime | None) -> str:
    if valor is None:
        return ""
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=UTC)
    return valor.astimezone(FUSO_HORARIO_BRASILIA).strftime("%d/%m/%Y %H:%M")
