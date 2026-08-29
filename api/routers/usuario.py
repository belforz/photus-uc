from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from api.deps import (
    get_atualizar_perfil_use_case,
    get_autenticar_usuario_use_case,
    get_cadastrar_usuario_use_case,
    get_usuario_id_atual,
)
from api.schemas.usuario import (
    AtualizarPerfilBody,
    AutenticarUsuarioBody,
    CadastrarUsuarioBody,
    TokenResponse,
    UsuarioAtualizado,
    UsuarioPublico,
)
from domain.application.dtos.usuario_dto import (
    AtualizarPerfilRequest,
    AutenticarUsuarioRequest,
    CadastrarUsuarioRequest,
)
from domain.application.use_cases.atualizar_perfil import AtualizarPerfil
from domain.application.use_cases.autenticar_usuario import AutenticarUsuario
from domain.application.use_cases.cadastrar_usuario import CadastrarUsuario

router = APIRouter(tags=["usuarios"])


@router.post(
    "/usuarios", response_model=UsuarioPublico, status_code=status.HTTP_201_CREATED
)
def cadastrar_usuario(
    body: CadastrarUsuarioBody,
    use_case: Annotated[CadastrarUsuario, Depends(get_cadastrar_usuario_use_case)],
) -> UsuarioPublico:
    resultado = use_case.execute(
        CadastrarUsuarioRequest(
            nome=body.nome,
            email=body.email,
            senha=body.senha,
            tipo_usuario=body.tipo_usuario,
        )
    )
    return UsuarioPublico(
        id=resultado.id,
        nome=resultado.nome,
        email=resultado.email,
        tipo_usuario=resultado.tipo_usuario,
        criado_em=resultado.criado_em,
    )


@router.post("/auth/login", response_model=TokenResponse)
def autenticar_usuario(
    body: AutenticarUsuarioBody,
    use_case: Annotated[AutenticarUsuario, Depends(get_autenticar_usuario_use_case)],
) -> TokenResponse:
    resultado = use_case.execute(
        AutenticarUsuarioRequest(email=body.email, senha=body.senha)
    )
    return TokenResponse(
        access_token=resultado.access_token,
        usuario_id=resultado.usuario_id,
        nome=resultado.nome,
        email=resultado.email,
        tipo_usuario=resultado.tipo_usuario,
    )


@router.patch("/usuarios/me", response_model=UsuarioAtualizado)
def atualizar_perfil(
    body: AtualizarPerfilBody,
    usuario_id: Annotated[str, Depends(get_usuario_id_atual)],
    use_case: Annotated[AtualizarPerfil, Depends(get_atualizar_perfil_use_case)],
) -> UsuarioAtualizado:
    resultado = use_case.execute(
        AtualizarPerfilRequest(
            usuario_id=usuario_id,
            nome=body.nome,
            email=body.email,
            senha=body.senha,
        )
    )
    return UsuarioAtualizado(
        id=resultado.id,
        nome=resultado.nome,
        email=resultado.email,
        tipo_usuario=resultado.tipo_usuario,
        atualizado_em=resultado.atualizado_em,
    )
