
from __future__ import annotations

from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, senha_plana: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def verify(self, senha_plana: str, senha_hash: str) -> bool:
        raise NotImplementedError
