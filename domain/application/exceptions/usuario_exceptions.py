

from __future__ import annotations


class UsuarioError(Exception):
    pass


class EmailJaCadastradoError(UsuarioError):
    pass


class CredenciaisInvalidasError(UsuarioError):
    pass


class UsuarioNaoEncontradoError(UsuarioError):
    pass
