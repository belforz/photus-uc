"""
Testes de UC01 — Cadastrar-se.
"""

from __future__ import annotations

import pytest

from domain.application.dtos.usuario_dto import CadastrarUsuarioRequest
from domain.application.exceptions.usuario_exceptions import EmailJaCadastradoError
from domain.application.use_cases.cadastrar_usuario import CadastrarUsuario
from domain.entities.usuario import TipoUsuario
from tests.fakes import FakePasswordHasher, FakeUsuarioRepository


@pytest.fixture
def use_case() -> CadastrarUsuario:
    return CadastrarUsuario(FakeUsuarioRepository(), FakePasswordHasher())


def test_cadastra_usuario_com_dados_validos(use_case: CadastrarUsuario) -> None:
    resposta = use_case.execute(
        CadastrarUsuarioRequest(
            nome="Leandro",
            email="leandro@teste.com",
            senha="SenhaForte#123",
            tipo_usuario=TipoUsuario.FOTOGRAFO,
        )
    )

    assert resposta.id
    assert resposta.nome == "Leandro"
    assert resposta.email == "leandro@teste.com"
    assert resposta.tipo_usuario == TipoUsuario.FOTOGRAFO


def test_rejeita_email_ja_cadastrado(use_case: CadastrarUsuario) -> None:
    request = CadastrarUsuarioRequest(
        nome="Leandro",
        email="leandro@teste.com",
        senha="SenhaForte#123",
        tipo_usuario=TipoUsuario.FOTOGRAFO,
    )
    use_case.execute(request)

    with pytest.raises(EmailJaCadastradoError):
        use_case.execute(request)


def test_nunca_persiste_senha_em_texto_plano(use_case: CadastrarUsuario) -> None:
    repository = use_case._usuario_repository  # type: ignore[attr-defined]
    resposta = use_case.execute(
        CadastrarUsuarioRequest(
            nome="Leandro",
            email="leandro@teste.com",
            senha="SenhaForte#123",
            tipo_usuario=TipoUsuario.FOTOGRAFO,
        )
    )

    usuario_salvo = repository.get_by_id(resposta.id)
    assert usuario_salvo is not None
    assert usuario_salvo.senha_hash != "SenhaForte#123"
