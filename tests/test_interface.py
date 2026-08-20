from comunicacao_proativa.configuracao import Configuracao
from comunicacao_proativa.infraestrutura.banco_dados import Base
from comunicacao_proativa.interface_web.aplicacao import criar_aplicacao


def test_painel_exibe_apenas_previsao_real(configuracao_teste, fabrica_sessoes):
    aplicacao = criar_aplicacao(configuracao_teste)
    resposta = aplicacao.test_client().get("/")
    assert resposta.status_code == 200
    assert "PREVISÃO REAL" in resposta.text
    assert "CONFIGURAÇÃO ATIVA" not in resposta.text
    assert "SIMULAÇÃO CONTROLADA" not in resposta.text


def test_csrf_bloqueia_post_sem_token(tmp_path):
    configuracao = Configuracao(
        BANCO_URL=f"sqlite:///{tmp_path / 'csrf.db'}",
        CHAVE_SECRETA="teste",
        CSRF_ATIVO=True,
        _env_file=None,
    )
    aplicacao = criar_aplicacao(configuracao)
    fabrica = aplicacao.extensions["fabrica_sessoes"]
    Base.metadata.create_all(fabrica.kw["bind"])
    assert aplicacao.test_client().post("/executar").status_code == 400
    fabrica.kw["bind"].dispose()
