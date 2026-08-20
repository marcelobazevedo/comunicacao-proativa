from comunicacao_proativa.interface_web.aplicacao import criar_aplicacao

aplicacao = criar_aplicacao()


if __name__ == "__main__":
    configuracao = aplicacao.extensions["configuracao_proativa"]
    aplicacao.run(host="0.0.0.0", port=configuracao.PORTA, debug=False)
