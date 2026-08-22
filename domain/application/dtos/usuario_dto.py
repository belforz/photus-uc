"""
DTOs de request/response para os use cases de Usuario (UC01–UC03).

São contratos de entrada/saída — não têm comportamento. Mantêm os use
cases desacoplados do formato exato de request usado na camada de API
(FastAPI/Pydantic, se for essa a escolha do front de acesso).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from domain.entities.usuario import TipoUsuario


# ---------------------------------------------------------------------------
# UC01 — Cadastrar-se
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CadastrarUsuarioRequest:
    nome: str
    email: str
    senha: str  # texto plano — hash é responsabilidade do PasswordHasher
    tipo_usuario: TipoUsuario


@dataclass(frozen=True)
class CadastrarUsuarioResponse:
    id: str
    nome: str
    email: str
    tipo_usuario: TipoUsuario
    criado_em: datetime


# ---------------------------------------------------------------------------
# UC02 — Autenticar-se
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AutenticarUsuarioRequest:
    email: str
    senha: str


@dataclass(frozen=True)
class AutenticarUsuarioResponse:
    access_token: str
    usuario_id: str
    nome: str
    email: str
    tipo_usuario: TipoUsuario


# ---------------------------------------------------------------------------
# UC03 — Atualizar perfil
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AtualizarPerfilRequest:
    usuario_id: str
    nome: str | None = None
    email: str | None = None
    senha: str | None = None  # se presente, re-hash é necessário


@dataclass(frozen=True)
class AtualizarPerfilResponse:
    id: str
    nome: str
    email: str
    tipo_usuario: TipoUsuario
    atualizado_em: datetime
