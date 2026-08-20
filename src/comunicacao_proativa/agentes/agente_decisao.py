from comunicacao_proativa.aplicacao.estado_fluxo import EstadoFluxo
from comunicacao_proativa.dominio.entidades import Destinatario
from comunicacao_proativa.dominio.regras import escolher_apolice
from comunicacao_proativa.infraestrutura.banco_dados import DecisaoModelo, agora_utc


class AgenteDecisao:
    def __init__(self, fabrica_sessoes) -> None:
        self.fabrica_sessoes = fabrica_sessoes

    def executar(self, estado: EstadoFluxo) -> dict:
        destinatarios = []
        decisoes = []
        segurados_com_evento = set()
        for segurado, evento in estado["eventos"]:
            segurados_com_evento.add(segurado.identificador)
            apolice = escolher_apolice(segurado, evento)
            if apolice:
                destinatarios.append(Destinatario(segurado, evento, apolice))
                motivo = f"Apólice {apolice.value} elegível para {evento.tipo.value}."
            else:
                motivo = f"Nenhuma apólice elegível para {evento.tipo.value}."
            decisoes.append((segurado.identificador, evento.tipo.value, bool(apolice), motivo))
        for segurado in estado["segurados"]:
            if segurado.identificador not in segurados_com_evento:
                decisoes.append(
                    (segurado.identificador, None, False, "Nenhum evento relevante na localidade.")
                )
        with self.fabrica_sessoes.begin() as sessao:
            for segurado_id, tipo_evento, elegivel, motivo in decisoes:
                sessao.add(
                    DecisaoModelo(
                        execucao_id=estado["identificador_execucao"],
                        segurado_id=segurado_id,
                        tipo_evento=tipo_evento,
                        elegivel=elegivel,
                        motivo=motivo,
                        decidida_em=agora_utc(),
                    )
                )
        return {"destinatarios": destinatarios}
