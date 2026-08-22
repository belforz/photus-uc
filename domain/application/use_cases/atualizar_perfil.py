"""
UC03 — Atualizar perfil.

Ator: Usuário Leigo / Fotógrafo (autenticado).
RFs relacionados: RF02.

Pré-condição: usuário autenticado (usuario_id vem de um token válido,
já decodificado antes deste use case ser chamado — decodificação de
token não é responsabilidade deste use case).
Fluxo principal:
    1. Usuário informa os campos que deseja atualizar (nome/email/senha,
       todos opcionais — atualização parcial).
    2. Sistema busca o usuário pelo id.
    3. Sistema aplica as mudanças informadas (se senha, re-hash).
    4. Sistema persiste a atualização.
    5. Sistema retorna os dados públicos atualizados.
Fluxo alternativo: usuario_id não encontrado → UsuarioNaoEncontradoError.
Fluxo alternativo: novo e-mail já pertence a outro usuário →
    EmailJaCadastradoError (reaproveitada de UC01).
"""

from __future__ import annotations

from datetime import UTC, datetime

from domain.application.dtos.usuario_dto import (
    AtualizarPerfilRequest,
    AtualizarPerfilResponse,
)
from domain.application.exceptions.usuario_exceptions import (
    EmailJaCadastradoError,
    UsuarioNaoEncontradoError,
)
from domain.application.interfaces.password_hasher import PasswordHasher
from domain.application.interfaces.usuario_repository import UsuarioRepository


class AtualizarPerfil:
    def __init__(
        self,
        usuario_repository: UsuarioRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._usuario_repository = usuario_repository
        self._password_hasher = password_hasher

    def execute(self, request: AtualizarPerfilRequest) -> AtualizarPerfilResponse:
        usuario = self._usuario_repository.get_by_id(request.usuario_id)
        if usuario is None:
            raise UsuarioNaoEncontradoError(request.usuario_id)

        if request.email is not None and request.email != usuario.email:
            outro = self._usuario_repository.get_by_email(request.email)
            if outro is not None and outro.id != usuario.id:
                raise EmailJaCadastradoError(request.email)
            usuario.email = request.email

        if request.nome is not None:
            usuario.nome = request.nome

        if request.senha is not None:
            usuario.senha_hash = self._password_hasher.hash(request.senha)

        usuario.atualizado_em = datetime.now(UTC)
        atualizado = self._usuario_repository.update(usuario)

        return AtualizarPerfilResponse(
            id=atualizado.id,
            nome=atualizado.nome,
            email=atualizado.email,
            tipo_usuario=atualizado.tipo_usuario,
            atualizado_em=atualizado.atualizado_em,
        )
