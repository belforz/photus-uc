"""
UC02 — Autenticar-se.

Ator: Usuário Leigo / Fotógrafo (não autenticado).
RFs relacionados: RF01.

Pré-condição: usuário já cadastrado (UC01).
Fluxo principal:
    1. Usuário informa e-mail e senha.
    2. Sistema busca usuário pelo e-mail.
    3. Sistema verifica a senha contra o hash armazenado.
    4. Sistema emite um token de sessão (JWT).
    5. Sistema retorna o token e os dados públicos do usuário.
Fluxo alternativo: e-mail não encontrado OU senha incorreta →
    CredenciaisInvalidasError (mensagem única, sem distinguir qual dos
    dois casos ocorreu — evita enumeração de contas).
"""

from __future__ import annotations

from domain.application.dtos.usuario_dto import (
    AutenticarUsuarioRequest,
    AutenticarUsuarioResponse,
)
from domain.application.exceptions.usuario_exceptions import (
    CredenciaisInvalidasError,
)
from domain.application.interfaces.password_hasher import PasswordHasher
from domain.application.interfaces.token_service import TokenService
from domain.application.interfaces.usuario_repository import UsuarioRepository


class AutenticarUsuario:
    def __init__(
        self,
        usuario_repository: UsuarioRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ) -> None:
        self._usuario_repository = usuario_repository
        self._password_hasher = password_hasher
        self._token_service = token_service

    def execute(self, request: AutenticarUsuarioRequest) -> AutenticarUsuarioResponse:
        usuario = self._usuario_repository.get_by_email(request.email)
        if usuario is None or not self._password_hasher.verify(
            request.senha, usuario.senha_hash
        ):
            raise CredenciaisInvalidasError()

        token = self._token_service.generate(usuario.id)

        return AutenticarUsuarioResponse(
            access_token=token,
            usuario_id=usuario.id,
            nome=usuario.nome,
            email=usuario.email,
            tipo_usuario=usuario.tipo_usuario,
        )
