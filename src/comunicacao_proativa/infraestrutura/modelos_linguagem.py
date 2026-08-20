import re
from time import sleep

import httpx
from pydantic import BaseModel, Field

from comunicacao_proativa.configuracao import Configuracao
from comunicacao_proativa.dominio.entidades import Destinatario, TipoEvento

RECOMENDACOES = {
    TipoEvento.CHUVA_INTENSA: "proteja objetos em áreas baixas e não atravesse vias alagadas",
    TipoEvento.VENTO_FORTE: "recolha objetos soltos e evite árvores e estruturas frágeis",
    TipoEvento.GRANIZO: "guarde o veículo em local coberto, se isso puder ser feito com segurança",
}
ROTULOS_EVENTOS = {
    TipoEvento.CHUVA_INTENSA: "chuva intensa",
    TipoEvento.VENTO_FORTE: "vento forte",
    TipoEvento.GRANIZO: "granizo",
}
ROTULOS_APOLICES = {
    "residencial": "residencial",
    "automovel": "automóvel",
}


class MensagemEstruturada(BaseModel):
    mensagem: str = Field(min_length=20, max_length=500)


class GeradorDeMensagem:
    def __init__(self, configuracao: Configuracao) -> None:
        self.configuracao = configuracao

    @property
    def nome_provedor(self) -> str:
        if self.configuracao.LOCAL:
            return f"ollama:{self.configuracao.OLLAMA_MODELO}"
        return f"groq:{self.configuracao.GROQ_MODELO}"

    def gerar(self, destinatario: Destinatario) -> str:
        instrucao = self._montar_instrucao(destinatario)
        ultimo_erro = None
        for tentativa in range(1, self.configuracao.LLM_MAXIMO_TENTATIVAS + 1):
            try:
                if self.configuracao.LOCAL:
                    resposta = self._consultar_ollama(instrucao)
                else:
                    resposta = self._consultar_groq(instrucao)
                mensagem = MensagemEstruturada.model_validate_json(resposta)
                return normalizar_mensagem(mensagem.mensagem)
            except Exception as erro:
                ultimo_erro = erro
                if tentativa < self.configuracao.LLM_MAXIMO_TENTATIVAS:
                    sleep(0.5 * tentativa)
        raise RuntimeError(
            f"LLM indisponível após {self.configuracao.LLM_MAXIMO_TENTATIVAS} tentativa(s)"
        ) from ultimo_erro

    def _montar_instrucao(self, destinatario: Destinatario) -> str:
        evento = destinatario.evento
        return (
            "Você redige alertas preventivos de uma seguradora. Responda somente com JSON no "
            'formato {"mensagem":"texto"}. A mensagem deve estar em português brasileiro, '
            "sem Markdown e sem emojis, com no máximo 500 caracteres, tom empático e sem "
            "alarmismo. "
            "Não prometa cobertura ou indenização. Inclua o fato meteorológico, data, recomendação "
            "e orientação para seguir autoridades em emergência. "
            f"Segurado: {destinatario.segurado.nome}. Cidade: {evento.cidade}. "
            f"Data: {evento.data.strftime('%d/%m/%Y')}. Evento: {ROTULOS_EVENTOS[evento.tipo]}. "
            f"Evidência: {evento.evidencia}. "
            f"Apólice: {ROTULOS_APOLICES[destinatario.apolice.value]}. "
            f"Recomendação: {RECOMENDACOES[evento.tipo]}."
        )

    def _consultar_ollama(self, instrucao: str) -> str:
        resposta = httpx.post(
            f"{self.configuracao.OLLAMA_URL.rstrip('/')}/api/chat",
            json={
                "model": self.configuracao.OLLAMA_MODELO,
                "messages": [{"role": "user", "content": instrucao}],
                "stream": False,
                "format": MensagemEstruturada.model_json_schema(),
                "options": {"temperature": self.configuracao.LLM_TEMPERATURA},
            },
            timeout=self.configuracao.LLM_TEMPO_LIMITE_SEGUNDOS,
        )
        resposta.raise_for_status()
        return resposta.json()["message"]["content"].strip()

    def _consultar_groq(self, instrucao: str) -> str:
        if not self.configuracao.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY não configurada")
        resposta = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.configuracao.GROQ_API_KEY}"},
            json={
                "model": self.configuracao.GROQ_MODELO,
                "messages": [{"role": "user", "content": instrucao}],
                "temperature": self.configuracao.LLM_TEMPERATURA,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "mensagem_preventiva",
                        "strict": True,
                        "schema": MensagemEstruturada.model_json_schema(),
                    },
                },
            },
            timeout=self.configuracao.LLM_TEMPO_LIMITE_SEGUNDOS,
        )
        resposta.raise_for_status()
        return resposta.json()["choices"][0]["message"]["content"].strip()


def mensagem_de_contingencia(destinatario: Destinatario) -> str:
    evento = destinatario.evento
    return (
        f"Olá, {destinatario.segurado.nome}! Há previsão de {ROTULOS_EVENTOS[evento.tipo]} "
        f"em {evento.cidade} em {evento.data.strftime('%d/%m/%Y')} ({evento.evidencia}). "
        f"Por prevenção, {RECOMENDACOES[evento.tipo]}. Em emergência, siga as autoridades locais."
    )


def normalizar_mensagem(mensagem: str) -> str:
    texto = re.sub(r"[*_`#]", "", mensagem)
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def validar_acesso_groq(configuracao: Configuracao) -> None:
    if not configuracao.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY não configurada")
    resposta = httpx.get(
        "https://api.groq.com/openai/v1/models",
        headers={"Authorization": f"Bearer {configuracao.GROQ_API_KEY}"},
        timeout=configuracao.LLM_TEMPO_LIMITE_SEGUNDOS,
    )
    resposta.raise_for_status()
    modelos = {item["id"] for item in resposta.json().get("data", [])}
    if configuracao.GROQ_MODELO not in modelos:
        raise RuntimeError(f"Modelo {configuracao.GROQ_MODELO} não disponível nesta conta")
