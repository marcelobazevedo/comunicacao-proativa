from datetime import date

from comunicacao_proativa.configuracao import Configuracao
from comunicacao_proativa.dominio.entidades import (
    Destinatario,
    EventoClimatico,
    Segurado,
    TipoApolice,
    TipoEvento,
)
from comunicacao_proativa.infraestrutura.modelos_linguagem import GeradorDeMensagem


class RespostaFalsa:
    def __init__(self, groq=False):
        self.groq = groq

    def raise_for_status(self):
        return None

    def json(self):
        if self.groq:
            return {
                "choices": [
                    {"message": {"content": '{"mensagem":"Mensagem remota segura para Ana."}'}}
                ]
            }
        return {"message": {"content": '{"mensagem":"Mensagem preventiva segura para Ana."}'}}


def test_ollama_usa_schema_e_resposta_estruturada(monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        "httpx.post", lambda *args, **kwargs: chamadas.append(kwargs) or RespostaFalsa()
    )
    segurado = Segurado(
        1, "Ana", "São Paulo", "SP", "BR", -23.5, -46.6, (TipoApolice.AUTOMOVEL,), "push"
    )
    evento = EventoClimatico(TipoEvento.GRANIZO, "São Paulo", date.today(), "alta", "WMO 96")
    gerador = GeradorDeMensagem(Configuracao(LOCAL=True, _env_file=None))
    assert gerador.gerar(Destinatario(segurado, evento, TipoApolice.AUTOMOVEL)).startswith(
        "Mensagem preventiva"
    )
    assert "format" in chamadas[0]["json"]


def test_groq_usa_schema_e_modelo_configurado(monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        "httpx.post", lambda *args, **kwargs: chamadas.append((args, kwargs)) or RespostaFalsa(True)
    )
    segurado = Segurado(
        1, "Ana", "São Paulo", "SP", "BR", -23.5, -46.6, (TipoApolice.AUTOMOVEL,), "email"
    )
    evento = EventoClimatico(TipoEvento.GRANIZO, "São Paulo", date.today(), "alta", "WMO 96")
    configuracao = Configuracao(
        LOCAL=False,
        GROQ_API_KEY="teste",
        GROQ_MODELO="openai/gpt-oss-20b",
        _env_file=None,
    )
    mensagem = GeradorDeMensagem(configuracao).gerar(
        Destinatario(segurado, evento, TipoApolice.AUTOMOVEL)
    )
    assert mensagem.startswith("Mensagem remota")
    assert chamadas[0][1]["json"]["response_format"]["type"] == "json_schema"
