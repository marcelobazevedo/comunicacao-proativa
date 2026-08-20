"""Validação e apresentação de contatos brasileiros."""

from re import compile as compilar

PADRAO_EMAIL = compilar(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def normalizar_email(valor: str) -> str:
    email = valor.strip().lower()
    if len(email) > 254 or not PADRAO_EMAIL.fullmatch(email):
        raise ValueError("Informe um endereço de e-mail válido.")
    return email


def normalizar_telefone(valor: str) -> str:
    digitos = "".join(caractere for caractere in valor if caractere.isdigit())
    if digitos.startswith("55") and len(digitos) in {12, 13}:
        digitos = digitos[2:]
    if len(digitos) not in {10, 11} or digitos[0] == "0" or digitos[2] == "0":
        raise ValueError("Informe um telefone brasileiro válido com DDD.")
    return f"55{digitos}"


def formatar_telefone(valor: str) -> str:
    digitos = "".join(caractere for caractere in valor if caractere.isdigit())
    if digitos.startswith("55") and len(digitos) in {12, 13}:
        digitos = digitos[2:]
    if len(digitos) == 11:
        return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"
    if len(digitos) == 10:
        return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"
    return valor
