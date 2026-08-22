from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.application.interfaces.usuario_repository import UsuarioRepository
from domain.entities.usuario import TipoUsuario, Usuario
from infra.db.models import UsuarioModel


class SQLAlchemyUsuarioRepository(UsuarioRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, usuario_id: str) -> Usuario | None:
        modelo = self._session.get(UsuarioModel, usuario_id)
        return _to_entity(modelo) if modelo is not None else None

    def get_by_email(self, email: str) -> Usuario | None:
        modelo = self._session.scalar(
            select(UsuarioModel).where(UsuarioModel.email == email)
        )
        return _to_entity(modelo) if modelo is not None else None

    def create(self, usuario: Usuario) -> Usuario:
        modelo = UsuarioModel(
            id=usuario.id,
            nome=usuario.nome,
            email=usuario.email,
            senha_hash=usuario.senha_hash,
            tipo_usuario=usuario.tipo_usuario.value,
            criado_em=usuario.criado_em,
            atualizado_em=usuario.atualizado_em,
        )
        self._session.add(modelo)
        self._session.commit()
        self._session.refresh(modelo)
        return _to_entity(modelo)

    def update(self, usuario: Usuario) -> Usuario:
        modelo = self._session.get(UsuarioModel, usuario.id)
        modelo.nome = usuario.nome
        modelo.email = usuario.email
        modelo.senha_hash = usuario.senha_hash
        modelo.tipo_usuario = usuario.tipo_usuario.value
        modelo.atualizado_em = usuario.atualizado_em
        self._session.commit()
        self._session.refresh(modelo)
        return _to_entity(modelo)


def _to_entity(modelo: UsuarioModel) -> Usuario:
    return Usuario(
        id=modelo.id,
        nome=modelo.nome,
        email=modelo.email,
        senha_hash=modelo.senha_hash,
        tipo_usuario=TipoUsuario(modelo.tipo_usuario),
        criado_em=modelo.criado_em,
        atualizado_em=modelo.atualizado_em,
    )
