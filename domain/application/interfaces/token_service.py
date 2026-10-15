
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TokenService(ABC):
    @abstractmethod
    def generate(self, usuario_id: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def decode(self, token: str) -> dict[str, Any]:
        raise NotImplementedError
