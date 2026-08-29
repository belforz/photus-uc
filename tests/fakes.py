"""
Fakes in-memory para os ports de Usuario, usados nos testes dos use
cases sem precisar de banco/bcrypt/JWT reais.

Esqueleto — comportamento mínimo o suficiente para os testes
compilarem; ajustar conforme a implementação real for definida.
"""

from __future__ import annotations

from domain.application.interfaces.password_hasher import PasswordHasher
from domain.application.interfaces.token_service import TokenService
from domain.application.interfaces.usuario_repository import UsuarioRepository
from domain.entities.usuario import Usuario


class FakeUsuarioRepository(UsuarioRepository):
    def __init__(self) -> None:
        self._por_id: dict[str, Usuario] = {}

    def get_by_id(self, usuario_id: str) -> Usuario | None:
        return self._por_id.get(usuario_id)

    def get_by_email(self, email: str) -> Usuario | None:
        return next((u for u in self._por_id.values() if u.email == email), None)

    def create(self, usuario: Usuario) -> Usuario:
        # TODO(Leandro): gerar id se usuario.id for None
        self._por_id[usuario.id] = usuario
        return usuario

    def update(self, usuario: Usuario) -> Usuario:
        self._por_id[usuario.id] = usuario
        return usuario


class FakePasswordHasher(PasswordHasher):
    """Fake burro — NÃO usar em produção. hash() é identidade prefixada."""

    def hash(self, senha_plana: str) -> str:
        return f"hashed::{senha_plana}"

    def verify(self, senha_plana: str, senha_hash: str) -> bool:
        return senha_hash == f"hashed::{senha_plana}"


class FakeTokenService(TokenService):
    def generate(self, usuario_id: str) -> str:
        return f"token::{usuario_id}"

    def decode(self, token: str) -> dict:
        return {"usuario_id": token.removeprefix("token::")}
