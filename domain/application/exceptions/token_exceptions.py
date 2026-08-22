"""
Exceção de domínio para falhas de validação de token (UC02/RNF09).

Levantada pela implementação concreta de TokenService (infra/) quando
o token é ausente, malformado ou expirado — a camada de API mapeia
para HTTP 401 sem precisar conhecer a lib de JWT usada.
"""

from __future__ import annotations


class TokenInvalidoError(Exception):
    """Token ausente, malformado ou expirado."""
