import json
from datetime import date
from time import perf_counter, sleep

import httpx

from comunicacao_proativa.dominio.entidades import Previsao, Segurado
from comunicacao_proativa.infraestrutura.banco_dados import ConsultaMeteorologicaModelo, agora_utc


class ProvedorOpenMeteo:
    ENDERECO = "https://api.open-meteo.com/v1/forecast"
    TOTAL_TENTATIVAS = 3

    def __init__(
        self,
        tempo_limite: float = 15,
        fabrica_sessoes=None,
        identificador_execucao: int | None = None,
    ) -> None:
        self.tempo_limite = tempo_limite
        self.fabrica_sessoes = fabrica_sessoes
        self.identificador_execucao = identificador_execucao

    def coletar(self, segurado: Segurado, dias: int = 3) -> list[Previsao]:
        parametros = {
            "latitude": segurado.latitude,
            "longitude": segurado.longitude,
            "daily": (
                "weather_code,precipitation_sum,precipitation_probability_max,wind_gusts_10m_max"
            ),
            "timezone": "America/Sao_Paulo",
            "forecast_days": dias,
        }
        resposta = self._consultar_com_novas_tentativas(segurado, parametros)
        diarios = resposta.json()["daily"]
        return [
            Previsao(
                segurado.cidade,
                date.fromisoformat(data),
                diarios["weather_code"][indice],
                diarios["precipitation_sum"][indice],
                diarios["precipitation_probability_max"][indice],
                diarios["wind_gusts_10m_max"][indice],
            )
            for indice, data in enumerate(diarios["time"])
        ]

    def _consultar_com_novas_tentativas(
        self, segurado: Segurado, parametros: dict
    ) -> httpx.Response:
        for tentativa in range(1, self.TOTAL_TENTATIVAS + 1):
            inicio = perf_counter()
            try:
                resposta = httpx.get(
                    self.ENDERECO,
                    params=parametros,
                    timeout=self.tempo_limite,
                )
                resposta.raise_for_status()
                self._registrar_consulta(
                    segurado,
                    parametros,
                    tentativa,
                    round((perf_counter() - inicio) * 1000),
                    "sucesso",
                    json.dumps(resposta.json(), ensure_ascii=False)[:20000],
                )
                return resposta
            except (httpx.TransportError, httpx.HTTPStatusError) as erro:
                self._registrar_consulta(
                    segurado,
                    parametros,
                    tentativa,
                    round((perf_counter() - inicio) * 1000),
                    "erro",
                    erro=str(erro),
                )
                if tentativa == self.TOTAL_TENTATIVAS:
                    raise RuntimeError(
                        f"Open-Meteo indisponível após {self.TOTAL_TENTATIVAS} tentativas"
                    ) from erro
                sleep(0.5 * tentativa)
        raise RuntimeError("Não foi possível consultar o Open-Meteo")

    def _registrar_consulta(
        self,
        segurado: Segurado,
        parametros: dict,
        tentativa: int,
        duracao_ms: int,
        status: str,
        resposta: str | None = None,
        erro: str | None = None,
    ) -> None:
        if self.fabrica_sessoes is None or self.identificador_execucao is None:
            return
        with self.fabrica_sessoes.begin() as sessao:
            sessao.add(
                ConsultaMeteorologicaModelo(
                    execucao_id=self.identificador_execucao,
                    segurado_id=segurado.identificador,
                    fonte="Open-Meteo",
                    parametros=json.dumps(parametros, ensure_ascii=False, sort_keys=True),
                    resposta=resposta,
                    status=status,
                    tentativa=tentativa,
                    duracao_ms=duracao_ms,
                    erro=erro,
                    consultada_em=agora_utc(),
                )
            )
