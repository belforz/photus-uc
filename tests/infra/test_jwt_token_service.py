from datetime import UTC, datetime, timedelta

import jwt
import pytest

from domain.application.exceptions.token_exceptions import TokenInvalidoError
from infra.security.jwt_token_service import JwtTokenService

SECRET = "x" * 32


def _token(**claims) -> str:
    return jwt.encode(claims, SECRET, algorithm="HS256")


def test_token_gerado_e_decodificado_devolve_o_usuario():
    service = JwtTokenService(secret=SECRET)
    assert service.decode(service.generate("u-1")) == {"usuario_id": "u-1"}


def test_tolera_pequeno_desvio_de_relogio_entre_emitir_e_validar():
    """Relógio recuando (ex.: WSL ressincronizando) deixa `iat` poucos segundos no futuro;
    um token válido não pode virar 401 por isso."""
    agora = datetime.now(UTC)
    token = _token(sub="u-1", iat=agora + timedelta(seconds=5), exp=agora + timedelta(minutes=5))
    assert JwtTokenService(secret=SECRET).decode(token) == {"usuario_id": "u-1"}


def test_iat_muito_no_futuro_continua_sendo_rejeitado():
    agora = datetime.now(UTC)
    token = _token(sub="u-1", iat=agora + timedelta(minutes=10), exp=agora + timedelta(minutes=20))
    with pytest.raises(TokenInvalidoError):
        JwtTokenService(secret=SECRET).decode(token)


def test_token_expirado_e_rejeitado():
    agora = datetime.now(UTC)
    token = _token(sub="u-1", iat=agora - timedelta(hours=2), exp=agora - timedelta(hours=1))
    with pytest.raises(TokenInvalidoError):
        JwtTokenService(secret=SECRET).decode(token)
