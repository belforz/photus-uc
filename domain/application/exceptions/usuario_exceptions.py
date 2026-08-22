"""
Exceções de domínio para os use cases de Usuario (UC01–UC03).

Ficam na camada de aplicação para que a camada de API (FastAPI, por
exemplo) possa mapeá-las para status HTTP sem os use cases precisarem
saber o que é HTTP.
"""

from __future__ import annotations


class UsuarioError(Exception):
    """Base para todas as exceções de domínio de Usuario."""


class EmailJaCadastradoError(UsuarioError):
    """UC01 — fluxo alternativo: e-mail já existe na base."""


class CredenciaisInvalidasError(UsuarioError):
    """UC02 — fluxo alternativo: e-mail não encontrado ou senha incorreta.

    Deliberadamente não distingue "email não existe" de "senha errada"
    na mensagem pública — evita enumeração de contas.
    """


class UsuarioNaoEncontradoError(UsuarioError):
    """UC03 — fluxo alternativo: usuario_id não corresponde a um registro."""
