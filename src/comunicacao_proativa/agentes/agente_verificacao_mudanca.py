"""Interrompe o fluxo quando a previsão ainda é idêntica à última consulta."""

import hashlib
import json

from sqlalchemy import select

from comunicacao_proativa.aplicacao.estado_fluxo import EstadoFluxo
from comunicacao_proativa.infraestrutura.banco_dados import (
    VerificacaoMeteorologicaModelo,
    agora_utc,
)


class AgenteVerificacaoMudanca:
    def __init__(self, fabrica_sessoes) -> None:
        self.fabrica_sessoes = fabrica_sessoes

    def executar(self, estado: EstadoFluxo) -> dict:
        registros = sorted(
            {
                (
                    segurado.latitude,
                    segurado.longitude,
                    previsao.data.isoformat(),
                    previsao.codigo_meteorologico,
                    previsao.precipitacao_mm,
                    previsao.probabilidade_precipitacao,
                    previsao.rajada_vento_kmh,
                )
                for segurado, previsao in estado["previsoes"]
            }
        )
        conteudo = json.dumps(registros, ensure_ascii=False, separators=(",", ":"))
        resumo = hashlib.sha256(conteudo.encode("utf-8")).hexdigest()
        with self.fabrica_sessoes.begin() as sessao:
            ultimo = sessao.scalar(
                select(VerificacaoMeteorologicaModelo)
                .order_by(VerificacaoMeteorologicaModelo.identificador.desc())
                .limit(1)
            )
            houve_mudanca = bool(registros) and (
                ultimo is None or ultimo.resumo_criptografico != resumo
            )
            sessao.add(
                VerificacaoMeteorologicaModelo(
                    execucao_id=estado["identificador_execucao"],
                    resumo_criptografico=resumo,
                    houve_mudanca=houve_mudanca,
                    verificada_em=agora_utc(),
                )
            )
        return {"houve_mudanca": houve_mudanca}
