"""
Entidade de domínio: Usuario.

Cobre RF01 (cadastro/autenticação) e RF02 (atualização de perfil) da
Proposta Técnica. Persistência real fica a cargo do adapter de
repositório (infra/), não desta classe.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TipoUsuario(str, Enum):
    LEIGO = "leigo"
    FOTOGRAFO = "fotografo"


@dataclass
class Usuario:
    id: str | None
    nome: str
    email: str
    senha_hash: str
    tipo_usuario: TipoUsuario
    criado_em: datetime
    atualizado_em: datetime
