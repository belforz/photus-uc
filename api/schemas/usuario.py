from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from domain.entities.usuario import TipoUsuario


class CadastrarUsuarioBody(BaseModel):
    nome: str = Field(min_length=1)
    email: EmailStr
    senha: str = Field(min_length=8)
    tipo_usuario: TipoUsuario


class UsuarioPublico(BaseModel):
    id: str
    nome: str
    email: str
    tipo_usuario: TipoUsuario
    criado_em: datetime


class AutenticarUsuarioBody(BaseModel):
    email: EmailStr
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario_id: str
    nome: str
    email: str
    tipo_usuario: TipoUsuario


class AtualizarPerfilBody(BaseModel):
    nome: str | None = Field(default=None, min_length=1)
    email: EmailStr | None = None
    senha: str | None = Field(default=None, min_length=8)


class UsuarioAtualizado(BaseModel):
    id: str
    nome: str
    email: str
    tipo_usuario: TipoUsuario
    atualizado_em: datetime
