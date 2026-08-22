"""
Adapter de TokenService usando PyJWT (UC02, RNF09).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from domain.application.exceptions.token_exceptions import TokenInvalidoError
from domain.application.interfaces.token_service import TokenService


class JwtTokenService(TokenService):
    def __init__(
        self,
        secret: str,
        expire_minutes: int = 60,
        algorithm: str = "HS256",
    ) -> None:
        self._secret = secret
        self._expire_minutes = expire_minutes
        self._algorithm = algorithm

    def generate(self, usuario_id: str) -> str:
        agora = datetime.now(UTC)
        payload = {
            "sub": usuario_id,
            "iat": agora,
            "exp": agora + timedelta(minutes=self._expire_minutes),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode(self, token: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except jwt.PyJWTError as exc:
            raise TokenInvalidoError(str(exc)) from exc
        return {"usuario_id": payload["sub"]}
