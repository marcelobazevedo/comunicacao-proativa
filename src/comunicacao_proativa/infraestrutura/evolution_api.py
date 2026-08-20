"""Integração de envio de mensagens com a Evolution API."""

import json
from dataclasses import dataclass
from time import sleep
from typing import Protocol

import httpx

from comunicacao_proativa.configuracao import Configuracao

STATUS_TEMPORARIOS = {408, 425, 429, 500, 502, 503, 504}


@dataclass(frozen=True)
class ResultadoEnvioWhatsapp:
    identificador_externo: str | None
    tentativas: int
    codigo_http: int
    resposta_resumo: str
    enviado: bool


class FalhaEnvioWhatsapp(RuntimeError):
    def __init__(self, mensagem: str, tentativas: int, codigo_http: int | None = None) -> None:
        super().__init__(mensagem)
        self.tentativas = tentativas
        self.codigo_http = codigo_http


class ProvedorEnvioWhatsapp(Protocol):
    @property
    def instancia(self) -> str | None: ...

    @property
    def envio_real(self) -> bool: ...

    def enviar(self, numero: str, mensagem: str) -> ResultadoEnvioWhatsapp: ...

    def diagnosticar(self) -> dict: ...


class ProvedorWhatsappSimulado:
    instancia = None
    envio_real = False

    def enviar(self, numero: str, mensagem: str) -> ResultadoEnvioWhatsapp:
        return ResultadoEnvioWhatsapp(None, 0, 0, "Envio simulado; nenhuma chamada externa.", False)

    def diagnosticar(self) -> dict:
        return {"ativo": False, "estado": "simulado"}


class ProvedorEvolutionApi:
    envio_real = True

    def __init__(self, configuracao: Configuracao) -> None:
        self.url = configuracao.EVOLUTION_API_URL.rstrip("/")
        self.chave = configuracao.EVOLUTION_API_KEY
        self.instancia = configuracao.EVOLUTION_API_INSTANCIA
        self.tempo_limite = configuracao.EVOLUTION_API_TEMPO_LIMITE_SEGUNDOS
        self.maximo_tentativas = configuracao.EVOLUTION_API_MAXIMO_TENTATIVAS

    @property
    def cabecalhos(self) -> dict[str, str]:
        return {"apikey": self.chave, "Content-Type": "application/json"}

    def diagnosticar(self) -> dict:
        resposta = httpx.get(
            f"{self.url}/instance/connectionState/{self.instancia}",
            headers=self.cabecalhos,
            timeout=self.tempo_limite,
        )
        resposta.raise_for_status()
        dados = resposta.json()
        estado = dados.get("instance", {}).get("state") or dados.get("state")
        return {"ativo": True, "instancia": self.instancia, "estado": estado, "resposta": dados}

    def enviar(self, numero: str, mensagem: str) -> ResultadoEnvioWhatsapp:
        ultimo_codigo = None
        ultimo_erro = "Falha desconhecida ao enviar pelo WhatsApp."
        for tentativa in range(1, self.maximo_tentativas + 1):
            try:
                resposta = httpx.post(
                    f"{self.url}/message/sendText/{self.instancia}",
                    headers=self.cabecalhos,
                    json={"number": numero, "text": mensagem},
                    timeout=self.tempo_limite,
                )
                ultimo_codigo = resposta.status_code
                if resposta.status_code in STATUS_TEMPORARIOS:
                    ultimo_erro = f"Evolution API respondeu HTTP {resposta.status_code}."
                    if tentativa < self.maximo_tentativas:
                        sleep(0.5 * tentativa)
                        continue
                resposta.raise_for_status()
                dados = resposta.json()
                resumo = json.dumps(dados, ensure_ascii=False)[:2000]
                identificador = dados.get("key", {}).get("id") or dados.get("id")
                return ResultadoEnvioWhatsapp(
                    str(identificador) if identificador else None,
                    tentativa,
                    resposta.status_code,
                    resumo,
                    True,
                )
            except (httpx.TimeoutException, httpx.TransportError) as erro:
                ultimo_erro = f"Falha temporária de comunicação: {erro.__class__.__name__}."
                if tentativa < self.maximo_tentativas:
                    sleep(0.5 * tentativa)
                    continue
            except httpx.HTTPStatusError as erro:
                raise FalhaEnvioWhatsapp(
                    f"Evolution API recusou o envio com HTTP {erro.response.status_code}.",
                    tentativa,
                    erro.response.status_code,
                ) from erro
            raise FalhaEnvioWhatsapp(ultimo_erro, tentativa, ultimo_codigo)
        raise FalhaEnvioWhatsapp(ultimo_erro, self.maximo_tentativas, ultimo_codigo)


def criar_provedor_whatsapp(configuracao: Configuracao) -> ProvedorEnvioWhatsapp:
    if configuracao.ENVIO_WHATSAPP_ATIVO:
        return ProvedorEvolutionApi(configuracao)
    return ProvedorWhatsappSimulado()
