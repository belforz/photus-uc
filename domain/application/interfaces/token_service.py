"""
Port de geração/validação de token de sessão (JWT).

Decisão já tomada (fora deste esqueleto): implementação concreta em
infra/security/ usando PyJWT. Este arquivo define só o contrato.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TokenService(ABC):
    @abstractmethod
    def generate(self, usuario_id: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def decode(self, token: str) -> dict[str, Any]:
        """Levanta exceção própria (não implementada aqui) se o token
        for inválido ou tiver expirado — decisão de qual exceção fica
        para a implementação em infra/."""
        raise NotImplementedError
