
from __future__ import annotations

import bcrypt

from domain.application.interfaces.password_hasher import PasswordHasher


class BcryptPasswordHasher(PasswordHasher):
    def hash(self, senha_plana: str) -> str:
        hash_bytes = bcrypt.hashpw(senha_plana.encode("utf-8"), bcrypt.gensalt())
        return hash_bytes.decode("utf-8")

    def verify(self, senha_plana: str, senha_hash: str) -> bool:
        return bcrypt.checkpw(senha_plana.encode("utf-8"), senha_hash.encode("utf-8"))
