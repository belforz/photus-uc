"""
UC01 — Cadastrar-se.

Ator: Usuário Leigo / Fotógrafo (não autenticado).
RFs relacionados: RF01.

Pré-condição: e-mail informado não pode já existir na base.
Fluxo principal:
    1. Usuário informa nome, e-mail, senha e tipo de usuário.
    2. Sistema valida unicidade do e-mail.
    3. Sistema faz hash da senha (nunca persiste texto plano).
    4. Sistema persiste o novo usuário.
    5. Sistema retorna os dados públicos do usuário criado.
Fluxo alternativo: e-mail já cadastrado → EmailJaCadastradoError.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from domain.application.dtos.usuario_dto import (
    CadastrarUsuarioRequest,
    CadastrarUsuarioResponse,
)
from domain.application.exceptions.usuario_exceptions import (
    EmailJaCadastradoError,
)
from domain.application.interfaces.password_hasher import PasswordHasher
from domain.application.interfaces.usuario_repository import UsuarioRepository
from domain.entities.usuario import Usuario


class CadastrarUsuario:
    def __init__(
        self,
        usuario_repository: UsuarioRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._usuario_repository = usuario_repository
        self._password_hasher = password_hasher

    def execute(self, request: CadastrarUsuarioRequest) -> CadastrarUsuarioResponse:
        if self._usuario_repository.get_by_email(request.email) is not None:
            raise EmailJaCadastradoError(request.email)

        agora = datetime.now(UTC)
        usuario = Usuario(
            id=str(uuid.uuid4()),
            nome=request.nome,
            email=request.email,
            senha_hash=self._password_hasher.hash(request.senha),
            tipo_usuario=request.tipo_usuario,
            criado_em=agora,
            atualizado_em=agora,
        )
        criado = self._usuario_repository.create(usuario)

        return CadastrarUsuarioResponse(
            id=criado.id,
            nome=criado.nome,
            email=criado.email,
            tipo_usuario=criado.tipo_usuario,
            criado_em=criado.criado_em,
        )
