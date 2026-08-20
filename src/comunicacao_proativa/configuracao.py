"""Configuração central da aplicação, carregada do arquivo .env."""

from functools import lru_cache
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from comunicacao_proativa.dominio.regras import ParametrosAlerta


class Configuracao(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    LOCAL: bool = True
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODELO: str = "ministral-3:14b"
    GROQ_API_KEY: str = ""
    GROQ_MODELO: str = "openai/gpt-oss-20b"
    LLM_TEMPERATURA: float = Field(default=0.2, ge=0, le=2)
    LLM_TEMPO_LIMITE_SEGUNDOS: float = Field(default=60, gt=0)
    LLM_MAXIMO_TENTATIVAS: int = Field(default=2, ge=1, le=5)
    BANCO_URL: str = "sqlite:///instancia/comunicacao_proativa.db"
    CHAVE_SECRETA: str = "desenvolvimento"
    PORTA: int = Field(default=5001, ge=1, le=65535)
    MONITORAMENTO_ATIVO: bool = True
    INTERVALO_MONITORAMENTO_MINUTOS: int = Field(default=30, ge=1)
    CANAL_NOTIFICACAO: str = Field(default="whatsapp", pattern="^(whatsapp|sms|email)$")
    ENVIO_WHATSAPP_ATIVO: bool = False
    EVOLUTION_API_URL: str = "http://127.0.0.1:8080"
    EVOLUTION_API_KEY: str = ""
    EVOLUTION_API_INSTANCIA: str = ""
    EVOLUTION_API_TEMPO_LIMITE_SEGUNDOS: float = Field(default=15, gt=0)
    EVOLUTION_API_MAXIMO_TENTATIVAS: int = Field(default=3, ge=1, le=5)
    CSRF_ATIVO: bool = True
    ALERTA_CHUVA_INTENSA_MM: float = Field(default=50, gt=0)
    ALERTA_CHUVA_COM_PROBABILIDADE_MM: float = Field(default=30, gt=0)
    ALERTA_PROBABILIDADE_MINIMA_CHUVA: int = Field(default=80, ge=0, le=100)
    ALERTA_VENTO_FORTE_KMH: float = Field(default=75, gt=0)
    ALERTA_VENTO_SEVERIDADE_ALTA_KMH: float = Field(default=90, gt=0)
    ALERTA_CODIGOS_WMO_GRANIZO: list[int] = Field(default_factory=lambda: [96, 99])

    @model_validator(mode="after")
    def validar_evolution_api(self) -> Self:
        if self.ENVIO_WHATSAPP_ATIVO and not all(
            [self.EVOLUTION_API_URL, self.EVOLUTION_API_KEY, self.EVOLUTION_API_INSTANCIA]
        ):
            raise ValueError(
                "O envio por WhatsApp exige EVOLUTION_API_URL, EVOLUTION_API_KEY e "
                "EVOLUTION_API_INSTANCIA."
            )
        return self

    def obter_parametros_alerta(self) -> ParametrosAlerta:
        if self.ALERTA_CHUVA_COM_PROBABILIDADE_MM > self.ALERTA_CHUVA_INTENSA_MM:
            raise ValueError(
                "ALERTA_CHUVA_COM_PROBABILIDADE_MM não pode superar ALERTA_CHUVA_INTENSA_MM."
            )
        if self.ALERTA_VENTO_SEVERIDADE_ALTA_KMH < self.ALERTA_VENTO_FORTE_KMH:
            raise ValueError(
                "ALERTA_VENTO_SEVERIDADE_ALTA_KMH não pode ser inferior a ALERTA_VENTO_FORTE_KMH."
            )
        return ParametrosAlerta(
            chuva_intensa_mm=self.ALERTA_CHUVA_INTENSA_MM,
            chuva_com_probabilidade_mm=self.ALERTA_CHUVA_COM_PROBABILIDADE_MM,
            probabilidade_minima_chuva=self.ALERTA_PROBABILIDADE_MINIMA_CHUVA,
            vento_forte_kmh=self.ALERTA_VENTO_FORTE_KMH,
            vento_severidade_alta_kmh=self.ALERTA_VENTO_SEVERIDADE_ALTA_KMH,
            codigos_wmo_granizo=frozenset(self.ALERTA_CODIGOS_WMO_GRANIZO),
        )


@lru_cache
def obter_configuracao() -> Configuracao:
    return Configuracao()
