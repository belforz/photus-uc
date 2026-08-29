from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.routers.usuario import router as usuario_router
from domain.application.exceptions.usuario_exceptions import (
    CredenciaisInvalidasError,
    EmailJaCadastradoError,
    UsuarioNaoEncontradoError,
)

app = FastAPI(title="Photus UC", version="0.1.0")
app.include_router(usuario_router)


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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
