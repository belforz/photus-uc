from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from domain.application.exceptions.token_exceptions import TokenInvalidoError
from domain.application.use_cases.atualizar_perfil import AtualizarPerfil
from domain.application.use_cases.autenticar_usuario import AutenticarUsuario
from domain.application.use_cases.cadastrar_usuario import CadastrarUsuario
from domain.application.use_cases.classify_semantic_anchor import ClassifySemanticAnchor
from domain.application.use_cases.submit_evaluation_batch import SubmitEvaluationBatch
from infra.clients.http_photus_b_client import HttpPhotusBClient
from infra.config import get_settings
from infra.db.evaluation_batch_repository import SQLAlchemyEvaluationBatchRepository
from infra.db.session import get_session
from infra.db.usuario_repository import SQLAlchemyUsuarioRepository
from infra.security.bcrypt_password_hasher import BcryptPasswordHasher
from infra.security.jwt_token_service import JwtTokenService
from infra.storage.filesystem_photo_storage import FilesystemPhotoStorage

_bearer_scheme = HTTPBearer(auto_error=False)


def get_password_hasher() -> BcryptPasswordHasher:
    return BcryptPasswordHasher()


def get_token_service() -> JwtTokenService:
    settings = get_settings()
    return JwtTokenService(
        secret=settings.jwt_secret, expire_minutes=settings.jwt_expire_minutes
    )


def get_usuario_repository(
    session: Annotated[Session, Depends(get_session)],
) -> SQLAlchemyUsuarioRepository:
    return SQLAlchemyUsuarioRepository(session)


def get_cadastrar_usuario_use_case(
    repo: Annotated[SQLAlchemyUsuarioRepository, Depends(get_usuario_repository)],
    hasher: Annotated[BcryptPasswordHasher, Depends(get_password_hasher)],
) -> CadastrarUsuario:
    return CadastrarUsuario(repo, hasher)


def get_autenticar_usuario_use_case(
    repo: Annotated[SQLAlchemyUsuarioRepository, Depends(get_usuario_repository)],
    hasher: Annotated[BcryptPasswordHasher, Depends(get_password_hasher)],
    token_service: Annotated[JwtTokenService, Depends(get_token_service)],
) -> AutenticarUsuario:
    return AutenticarUsuario(repo, hasher, token_service)


def get_atualizar_perfil_use_case(
    repo: Annotated[SQLAlchemyUsuarioRepository, Depends(get_usuario_repository)],
    hasher: Annotated[BcryptPasswordHasher, Depends(get_password_hasher)],
) -> AtualizarPerfil:
    return AtualizarPerfil(repo, hasher)


def get_evaluation_batch_repository(
    session: Annotated[Session, Depends(get_session)],
) -> SQLAlchemyEvaluationBatchRepository:
    return SQLAlchemyEvaluationBatchRepository(session)


def get_photo_storage() -> FilesystemPhotoStorage:
    settings = get_settings()
    return FilesystemPhotoStorage(base_dir=settings.uploads_dir)


def get_photus_b_client() -> HttpPhotusBClient:
    settings = get_settings()
    return HttpPhotusBClient(
        base_url=settings.photus_b_base_url,
        timeout_seconds=settings.photus_b_timeout_seconds,
    )


def get_classify_semantic_anchor_use_case(
    repo: Annotated[
        SQLAlchemyEvaluationBatchRepository, Depends(get_evaluation_batch_repository)
    ],
    client: Annotated[HttpPhotusBClient, Depends(get_photus_b_client)],
) -> ClassifySemanticAnchor:
    return ClassifySemanticAnchor(repo, client)


def get_submit_evaluation_batch_use_case(
    repo: Annotated[
        SQLAlchemyEvaluationBatchRepository, Depends(get_evaluation_batch_repository)
    ],
    storage: Annotated[FilesystemPhotoStorage, Depends(get_photo_storage)],
    classify_semantic_anchor: Annotated[
        ClassifySemanticAnchor, Depends(get_classify_semantic_anchor_use_case)
    ],
) -> SubmitEvaluationBatch:
    return SubmitEvaluationBatch(repo, storage, classify_semantic_anchor)


def get_usuario_id_atual(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    token_service: Annotated[JwtTokenService, Depends(get_token_service)],
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não informado",
        )
    try:
        payload = token_service.decode(credentials.credentials)
    except TokenInvalidoError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        ) from exc
    return payload["usuario_id"]
