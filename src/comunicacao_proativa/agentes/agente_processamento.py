from comunicacao_proativa.aplicacao.estado_fluxo import EstadoFluxo


class AgenteProcessamento:
    def executar(self, estado: EstadoFluxo) -> dict:
        unicos = {}
        for segurado, previsao in estado["previsoes"]:
            chave = (segurado.identificador, previsao.data)
            unicos[chave] = (segurado, previsao)
        return {"previsoes": list(unicos.values())}
