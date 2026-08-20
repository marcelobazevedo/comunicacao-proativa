import pytest

from comunicacao_proativa.dominio.contatos import (
    formatar_telefone,
    normalizar_email,
    normalizar_telefone,
)


def test_normaliza_contatos_para_uso_futuro():
    assert normalizar_email(" ANA@Exemplo.COM ") == "ana@exemplo.com"
    assert normalizar_telefone("(11) 99999-9999") == "5511999999999"
    assert normalizar_telefone("+55 11 99999-9999") == "5511999999999"
    assert formatar_telefone("5511999999999") == "(11) 99999-9999"


@pytest.mark.parametrize("valor", ["sem-arroba", "nome@", "@exemplo.com"])
def test_rejeita_email_invalido(valor):
    with pytest.raises(ValueError):
        normalizar_email(valor)


@pytest.mark.parametrize("valor", ["9999-9999", "0011999999999", "telefone"])
def test_rejeita_telefone_sem_ddd_valido(valor):
    with pytest.raises(ValueError):
        normalizar_telefone(valor)
