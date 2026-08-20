"""Conversão de cidade e UF em coordenadas pela API pública Open-Meteo."""

import unicodedata
from dataclasses import dataclass

import httpx

ESTADOS = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AP": "Amapá",
    "AM": "Amazonas",
    "BA": "Bahia",
    "CE": "Ceará",
    "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    "GO": "Goiás",
    "MA": "Maranhão",
    "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais",
    "PA": "Pará",
    "PB": "Paraíba",
    "PR": "Paraná",
    "PE": "Pernambuco",
    "PI": "Piauí",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul",
    "RO": "Rondônia",
    "RR": "Roraima",
    "SC": "Santa Catarina",
    "SP": "São Paulo",
    "SE": "Sergipe",
    "TO": "Tocantins",
}


@dataclass(frozen=True)
class LocalizacaoGeografica:
    cidade: str
    estado: str
    pais: str
    latitude: float
    longitude: float


class CidadeNaoEncontrada(ValueError):
    pass


def _normalizar(texto: str) -> str:
    sem_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sem_acentos.casefold().strip()


class GeocodificadorOpenMeteo:
    ENDERECO = "https://geocoding-api.open-meteo.com/v1/search"

    def __init__(self, tempo_limite: float = 10) -> None:
        self.tempo_limite = tempo_limite

    def buscar(self, cidade: str, estado: str) -> LocalizacaoGeografica:
        uf = estado.strip().upper()
        if uf not in ESTADOS:
            raise CidadeNaoEncontrada("Informe uma UF brasileira válida.")
        resposta = httpx.get(
            self.ENDERECO,
            params={"name": cidade.strip(), "count": 20, "language": "pt", "countryCode": "BR"},
            timeout=self.tempo_limite,
        )
        resposta.raise_for_status()
        resultados = resposta.json().get("results", [])
        nome_estado = _normalizar(ESTADOS[uf])
        correspondencias = [
            item
            for item in resultados
            if item.get("country_code") == "BR"
            and _normalizar(item.get("admin1", "")) == nome_estado
        ]
        if not correspondencias:
            raise CidadeNaoEncontrada(f"Não encontramos '{cidade}' em {uf}.")
        item = correspondencias[0]
        return LocalizacaoGeografica(item["name"], uf, "BR", item["latitude"], item["longitude"])
