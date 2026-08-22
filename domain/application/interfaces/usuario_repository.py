"""
Port de persistência para Usuario.

A implementação concreta (ex.: SQLAlchemy, asyncpg, etc.) vive em
infra/ e é injetada nos use cases — os use cases nunca importam
uma implementação concreta diretamente.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.usuario import Usuario


class UsuarioRepository(ABC):
    @abstractmethod
    def get_by_id(self, usuario_id: str) -> Usuario | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_email(self, email: str) -> Usuario | None:
        raise NotImplementedError

    @abstractmethod
    def create(self, usuario: Usuario) -> Usuario:
        raise NotImplementedError

    @abstractmethod
    def update(self, usuario: Usuario) -> Usuario:
        raise NotImplementedError
