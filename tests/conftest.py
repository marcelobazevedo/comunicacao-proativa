import pytest

from comunicacao_proativa.configuracao import Configuracao
from comunicacao_proativa.infraestrutura.banco_dados import (
    Base,
    criar_dados_iniciais,
    criar_fabrica_sessoes,
)


@pytest.fixture
def configuracao_teste(tmp_path):
    return Configuracao(
        BANCO_URL=f"sqlite:///{tmp_path / 'teste.db'}",
        LOCAL=True,
        CHAVE_SECRETA="teste",
        CSRF_ATIVO=False,
        _env_file=None,
    )


@pytest.fixture
def fabrica_sessoes(configuracao_teste):
    fabrica = criar_fabrica_sessoes(configuracao_teste)
    Base.metadata.create_all(fabrica.kw["bind"])
    criar_dados_iniciais(fabrica)
    yield fabrica
    fabrica.kw["bind"].dispose()
