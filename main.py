from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.routers.evaluation_batch import router as evaluation_batch_router
from api.routers.usuario import router as usuario_router
from domain.application.exceptions.evaluation_batch_exceptions import (
    NoPhotosAttachedError,
    PhotoLimitExceededError,
)
from domain.application.exceptions.usuario_exceptions import (
    CredenciaisInvalidasError,
    EmailJaCadastradoError,
    UsuarioNaoEncontradoError,
)

app = FastAPI(title="Photus UC", version="0.1.0")
app.include_router(usuario_router)
app.include_router(evaluation_batch_router)


@app.exception_handler(EmailJaCadastradoError)
def _email_ja_cadastrado(request: Request, exc: EmailJaCadastradoError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": "E-mail já cadastrado"})


@app.exception_handler(CredenciaisInvalidasError)
def _credenciais_invalidas(
    request: Request, exc: CredenciaisInvalidasError
) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": "Credenciais inválidas"})


@app.exception_handler(UsuarioNaoEncontradoError)
def _usuario_nao_encontrado(
    request: Request, exc: UsuarioNaoEncontradoError
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "Usuário não encontrado"})


@app.exception_handler(NoPhotosAttachedError)
def _no_photos_attached(request: Request, exc: NoPhotosAttachedError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": "Nenhuma fotografia anexada"})


@app.exception_handler(PhotoLimitExceededError)
def _photo_limit_exceeded(request: Request, exc: PhotoLimitExceededError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"detail": f"Limite de {exc.limit} fotografias excedido"},
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
