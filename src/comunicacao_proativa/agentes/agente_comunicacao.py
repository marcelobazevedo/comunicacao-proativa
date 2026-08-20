from comunicacao_proativa.aplicacao.estado_fluxo import EstadoFluxo
from comunicacao_proativa.dominio.entidades import MensagemGerada
from comunicacao_proativa.infraestrutura.banco_dados import MensagemModelo, agora_utc
from comunicacao_proativa.infraestrutura.modelos_linguagem import mensagem_de_contingencia


class AgenteComunicacao:
    def __init__(self, gerador, fabrica_sessoes) -> None:
        self.gerador = gerador
        self.fabrica_sessoes = fabrica_sessoes

    def executar(self, estado: EstadoFluxo) -> dict:
        mensagens = []
        erros = list(estado.get("erros", []))
        for destinatario in estado["destinatarios"]:
            provedor = self.gerador.nome_provedor
            try:
                conteudo = self.gerador.gerar(destinatario)
            except Exception as erro:
                erros.append(f"LLM indisponível para {destinatario.segurado.nome}: {erro}")
                conteudo = mensagem_de_contingencia(destinatario)
                provedor = "contingencia"
            mensagens.append(MensagemGerada(destinatario, conteudo, provedor))
        with self.fabrica_sessoes.begin() as sessao:
            for item in mensagens:
                sessao.add(
                    MensagemModelo(
                        execucao_id=estado["identificador_execucao"],
                        segurado_id=item.destinatario.segurado.identificador,
                        tipo_evento=item.destinatario.evento.tipo.value,
                        conteudo=item.conteudo,
                        provedor_modelo=item.provedor_modelo,
                        criada_em=agora_utc(),
                    )
                )
        return {"mensagens": mensagens, "erros": erros}
