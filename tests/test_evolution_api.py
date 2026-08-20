import httpx
import pytest
from pydantic import ValidationError

from comunicacao_proativa.configuracao import Configuracao
from comunicacao_proativa.infraestrutura.evolution_api import ProvedorEvolutionApi


def configuracao_evolution(**alteracoes):
    valores = {
        "ENVIO_WHATSAPP_ATIVO": True,
        "EVOLUTION_API_URL": "http://evolution:8080",
        "EVOLUTION_API_KEY": "chave-teste",
        "EVOLUTION_API_INSTANCIA": "protege-antes",
        "EVOLUTION_API_MAXIMO_TENTATIVAS": 2,
        "_env_file": None,
    }
    valores.update(alteracoes)
    return Configuracao(**valores)


def resposta(codigo, dados):
    return httpx.Response(
        codigo,
        json=dados,
        request=httpx.Request("POST", "http://evolution:8080"),
    )


def test_envio_real_usa_endpoint_chave_e_retentativa(monkeypatch):
    chamadas = []
    respostas = [resposta(503, {"erro": "temporário"}), resposta(201, {"key": {"id": "abc"}})]

    def postar(*args, **kwargs):
        chamadas.append((args, kwargs))
        return respostas.pop(0)

    monkeypatch.setattr("httpx.post", postar)
    monkeypatch.setattr("comunicacao_proativa.infraestrutura.evolution_api.sleep", lambda _: None)
    resultado = ProvedorEvolutionApi(configuracao_evolution()).enviar(
        "5511999999999", "Mensagem preventiva"
    )
    assert resultado.enviado
    assert resultado.tentativas == 2
    assert resultado.identificador_externo == "abc"
    assert chamadas[0][0][0].endswith("/message/sendText/protege-antes")
    assert chamadas[0][1]["headers"]["apikey"] == "chave-teste"
    assert chamadas[0][1]["json"] == {
        "number": "5511999999999",
        "text": "Mensagem preventiva",
    }


def test_diagnostico_consulta_estado_da_instancia(monkeypatch):
    monkeypatch.setattr(
        "httpx.get", lambda *args, **kwargs: resposta(200, {"instance": {"state": "open"}})
    )
    resultado = ProvedorEvolutionApi(configuracao_evolution()).diagnosticar()
    assert resultado["estado"] == "open"


def test_configuracao_ativa_exige_credenciais():
    with pytest.raises(ValidationError):
        Configuracao(
            ENVIO_WHATSAPP_ATIVO=True,
            EVOLUTION_API_KEY="",
            EVOLUTION_API_INSTANCIA="",
            _env_file=None,
        )
