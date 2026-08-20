from comunicacao_proativa.aplicacao.estado_fluxo import EstadoFluxo
from comunicacao_proativa.dominio.regras import detectar_eventos


class AgenteAnaliseRisco:
    def __init__(self, parametros_alerta) -> None:
        self.parametros_alerta = parametros_alerta

    def executar(self, estado: EstadoFluxo) -> dict:
        eventos = []
        for segurado, previsao in estado["previsoes"]:
            eventos.extend(
                (segurado, evento) for evento in detectar_eventos(previsao, self.parametros_alerta)
            )
        return {"eventos": eventos}
