"""
Port de hashing de senha.

Decisão já tomada (fora deste esqueleto): implementação concreta em
infra/security/ usando passlib + bcrypt
(ex.: `passlib.context.CryptContext(schemes=["bcrypt"])`).
Este arquivo define só o contrato que o use case depende.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, senha_plana: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def verify(self, senha_plana: str, senha_hash: str) -> bool:
        raise NotImplementedError
