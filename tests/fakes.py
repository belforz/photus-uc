"""
Fakes in-memory para os ports de Usuario, usados nos testes dos use
cases sem precisar de banco/bcrypt/JWT reais.

Esqueleto — comportamento mínimo o suficiente para os testes
compilarem; ajustar conforme a implementação real for definida.
"""

from __future__ import annotations

from domain.application.interfaces.evaluation_batch_repository import (
    EvaluationBatchRepository,
)
from domain.application.interfaces.password_hasher import PasswordHasher
from domain.application.interfaces.photo_storage import PhotoStorage
from domain.application.interfaces.photus_b_client import PhotusBClient, SemanticClassification
from domain.application.interfaces.token_service import TokenService
from domain.application.interfaces.usuario_repository import UsuarioRepository
from domain.entities.evaluated_photo import EvaluatedPhoto
from domain.entities.evaluation_batch import EvaluationBatch
from domain.entities.usuario import Usuario


class FakeUsuarioRepository(UsuarioRepository):
    def __init__(self) -> None:
        self._por_id: dict[str, Usuario] = {}

    def get_by_id(self, usuario_id: str) -> Usuario | None:
        return self._por_id.get(usuario_id)

    def get_by_email(self, email: str) -> Usuario | None:
        return next((u for u in self._por_id.values() if u.email == email), None)

    def create(self, usuario: Usuario) -> Usuario:
        # TODO(Leandro): gerar id se usuario.id for None
        self._por_id[usuario.id] = usuario
        return usuario

    def update(self, usuario: Usuario) -> Usuario:
        self._por_id[usuario.id] = usuario
        return usuario


class FakePasswordHasher(PasswordHasher):
    """Fake burro — NÃO usar em produção. hash() é identidade prefixada."""

    def hash(self, senha_plana: str) -> str:
        return f"hashed::{senha_plana}"

    def verify(self, senha_plana: str, senha_hash: str) -> bool:
        return senha_hash == f"hashed::{senha_plana}"


class FakeTokenService(TokenService):
    def generate(self, usuario_id: str) -> str:
        return f"token::{usuario_id}"

    def decode(self, token: str) -> dict:
        return {"usuario_id": token.removeprefix("token::")}


class FakeEvaluationBatchRepository(EvaluationBatchRepository):
    def __init__(self) -> None:
        self._batches: dict[str, EvaluationBatch] = {}
        self._photos: dict[str, list[EvaluatedPhoto]] = {}

    def create(self, batch: EvaluationBatch) -> EvaluationBatch:
        self._batches[batch.id] = batch
        self._photos.setdefault(batch.id, [])
        return batch

    def get_by_id(self, batch_id: str) -> EvaluationBatch | None:
        return self._batches.get(batch_id)

    def add_photos(self, photos: list[EvaluatedPhoto]) -> list[EvaluatedPhoto]:
        for photo in photos:
            self._photos.setdefault(photo.batch_id, []).append(photo)
        return photos

    def update_classification(self, batch: EvaluationBatch) -> EvaluationBatch:
        self._batches[batch.id] = batch
        return batch


class FakePhotoStorage(PhotoStorage):
    def __init__(self) -> None:
        self.saved: list[tuple[str, str, bytes]] = []

    def save(self, batch_id: str, file_name: str, content: bytes) -> str:
        self.saved.append((batch_id, file_name, content))
        return f"/fake/{batch_id}/{file_name}"


class FakePhotusBClient(PhotusBClient):
    """Fake configurável — devolve um resultado fixo ou levanta uma exceção fixa."""

    def __init__(
        self,
        result: SemanticClassification | None = None,
        error: Exception | None = None,
    ) -> None:
        self._result = result
        self._error = error

    def classify_text(self, text: str) -> SemanticClassification:
        if self._error is not None:
            raise self._error
        assert self._result is not None
        return self._result
