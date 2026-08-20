from comunicacao_proativa.aplicacao.estado_fluxo import EstadoFluxo


class AgenteColeta:
    def __init__(self, provedor) -> None:
        self.provedor = provedor

    def executar(self, estado: EstadoFluxo) -> dict:
        previsoes = []
        erros = list(estado.get("erros", []))
        for segurado in estado["segurados"]:
            try:
                previsoes.extend(
                    (segurado, previsao) for previsao in self.provedor.coletar(segurado)
                )
            except Exception as erro:
                erros.append(f"Falha na coleta de {segurado.cidade}: {erro}")
        return {"previsoes": previsoes, "erros": erros}
