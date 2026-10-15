
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
