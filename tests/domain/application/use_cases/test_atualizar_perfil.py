"""
Testes de UC03 — Atualizar perfil.
"""

from __future__ import annotations

import pytest

from domain.application.dtos.usuario_dto import (
    AtualizarPerfilRequest,
    CadastrarUsuarioRequest,
)
from domain.application.exceptions.usuario_exceptions import (
    EmailJaCadastradoError,
    UsuarioNaoEncontradoError,
)
from domain.application.use_cases.atualizar_perfil import AtualizarPerfil
from domain.application.use_cases.cadastrar_usuario import CadastrarUsuario
from domain.entities.usuario import TipoUsuario
from tests.fakes import FakePasswordHasher, FakeUsuarioRepository


@pytest.fixture
def repository() -> FakeUsuarioRepository:
    return FakeUsuarioRepository()


@pytest.fixture
def use_case(repository: FakeUsuarioRepository) -> AtualizarPerfil:
    return AtualizarPerfil(repository, FakePasswordHasher())


def _cadastrar(repository: FakeUsuarioRepository, email: str = "leandro@teste.com") -> str:
    resposta = CadastrarUsuario(repository, FakePasswordHasher()).execute(
        CadastrarUsuarioRequest(
            nome="Leandro",
            email=email,
            senha="SenhaForte#123",
            tipo_usuario=TipoUsuario.FOTOGRAFO,
        )
    )
    return resposta.id


def test_atualiza_nome(use_case: AtualizarPerfil, repository: FakeUsuarioRepository) -> None:
    usuario_id = _cadastrar(repository)

    resposta = use_case.execute(
        AtualizarPerfilRequest(usuario_id=usuario_id, nome="Leandro Belfor")
    )

    assert resposta.nome == "Leandro Belfor"
    assert resposta.email == "leandro@teste.com"


def test_atualiza_senha_com_rehash(
    use_case: AtualizarPerfil, repository: FakeUsuarioRepository
) -> None:
    usuario_id = _cadastrar(repository)
    hash_antigo = repository.get_by_id(usuario_id).senha_hash

    use_case.execute(AtualizarPerfilRequest(usuario_id=usuario_id, senha="OutraSenha#456"))

    hash_novo = repository.get_by_id(usuario_id).senha_hash
    assert hash_novo != hash_antigo


def test_rejeita_usuario_inexistente(use_case: AtualizarPerfil) -> None:
    with pytest.raises(UsuarioNaoEncontradoError):
        use_case.execute(AtualizarPerfilRequest(usuario_id="inexistente", nome="X"))


def test_rejeita_troca_para_email_ja_usado_por_outro_usuario(
    use_case: AtualizarPerfil, repository: FakeUsuarioRepository
) -> None:
    usuario_id = _cadastrar(repository, email="leandro@teste.com")
    _cadastrar(repository, email="outro@teste.com")

    with pytest.raises(EmailJaCadastradoError):
        use_case.execute(
            AtualizarPerfilRequest(usuario_id=usuario_id, email="outro@teste.com")
        )


def test_atualizacao_parcial_nao_apaga_campos_nao_informados(
    use_case: AtualizarPerfil, repository: FakeUsuarioRepository
) -> None:
    usuario_id = _cadastrar(repository)

    resposta = use_case.execute(
        AtualizarPerfilRequest(usuario_id=usuario_id, nome="Só o nome mudou")
    )

    assert resposta.nome == "Só o nome mudou"
    assert resposta.email == "leandro@teste.com"
