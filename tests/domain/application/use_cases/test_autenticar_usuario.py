"""
Testes de UC02 — Autenticar-se.
"""

from __future__ import annotations

import pytest

from domain.application.dtos.usuario_dto import (
    AutenticarUsuarioRequest,
    CadastrarUsuarioRequest,
)
from domain.application.exceptions.usuario_exceptions import CredenciaisInvalidasError
from domain.application.use_cases.autenticar_usuario import AutenticarUsuario
from domain.application.use_cases.cadastrar_usuario import CadastrarUsuario
from domain.entities.usuario import TipoUsuario
from tests.fakes import FakePasswordHasher, FakeTokenService, FakeUsuarioRepository


@pytest.fixture
def repository() -> FakeUsuarioRepository:
    return FakeUsuarioRepository()


@pytest.fixture
def use_case(repository: FakeUsuarioRepository) -> AutenticarUsuario:
    return AutenticarUsuario(repository, FakePasswordHasher(), FakeTokenService())


def _cadastrar(repository: FakeUsuarioRepository) -> None:
    CadastrarUsuario(repository, FakePasswordHasher()).execute(
        CadastrarUsuarioRequest(
            nome="Leandro",
            email="leandro@teste.com",
            senha="SenhaForte#123",
            tipo_usuario=TipoUsuario.FOTOGRAFO,
        )
    )


def test_autentica_com_credenciais_validas(
    use_case: AutenticarUsuario, repository: FakeUsuarioRepository
) -> None:
    _cadastrar(repository)

    resposta = use_case.execute(
        AutenticarUsuarioRequest(email="leandro@teste.com", senha="SenhaForte#123")
    )

    assert resposta.access_token
    assert resposta.email == "leandro@teste.com"


def test_rejeita_email_inexistente(use_case: AutenticarUsuario) -> None:
    with pytest.raises(CredenciaisInvalidasError):
        use_case.execute(
            AutenticarUsuarioRequest(email="ninguem@teste.com", senha="qualquer")
        )


def test_rejeita_senha_incorreta(
    use_case: AutenticarUsuario, repository: FakeUsuarioRepository
) -> None:
    _cadastrar(repository)

    with pytest.raises(CredenciaisInvalidasError):
        use_case.execute(
            AutenticarUsuarioRequest(email="leandro@teste.com", senha="senha-errada")
        )


def test_mensagem_de_erro_nao_distingue_email_de_senha(
    use_case: AutenticarUsuario, repository: FakeUsuarioRepository
) -> None:
    _cadastrar(repository)

    with pytest.raises(CredenciaisInvalidasError) as email_inexistente:
        use_case.execute(
            AutenticarUsuarioRequest(email="ninguem@teste.com", senha="qualquer")
        )

    with pytest.raises(CredenciaisInvalidasError) as senha_errada:
        use_case.execute(
            AutenticarUsuarioRequest(email="leandro@teste.com", senha="senha-errada")
        )

    assert str(email_inexistente.value) == str(senha_errada.value)
