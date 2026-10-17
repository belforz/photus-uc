
from __future__ import annotations

from domain.application.interfaces.evaluation_batch_repository import (
    EvaluationBatchRepository,
)
from domain.application.interfaces.password_hasher import PasswordHasher
from domain.application.interfaces.photo_evaluation_pipeline import (
    PhotoEvaluationPipeline,
    PhotoToEvaluate,
    PipelineOutcome,
)
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

    def list_photos(self, batch_id: str) -> list[EvaluatedPhoto]:
        return list(self._photos.get(batch_id, []))

    def update_photo_evaluations(self, photos: list[EvaluatedPhoto]) -> list[EvaluatedPhoto]:
        for photo in photos:
            lote = self._photos.setdefault(photo.batch_id, [])
            for i, existing in enumerate(lote):
                if existing.id == photo.id:
                    lote[i] = photo
        return photos

    def update_status(self, batch: EvaluationBatch) -> EvaluationBatch:
        self._batches[batch.id] = batch
        return batch

    def list_by_user(self, user_id: str) -> list[EvaluationBatch]:
        mine = [b for b in self._batches.values() if b.user_id == user_id]
        return sorted(mine, key=lambda b: b.created_at, reverse=True)

    def count_photos(self, batch_ids: list[str]) -> dict[str, int]:
        return {bid: len(self._photos.get(bid, [])) for bid in batch_ids}

    def delete(self, batch_id: str) -> None:
        self._batches.pop(batch_id, None)
        self._photos.pop(batch_id, None)


class FakePhotoEvaluationPipeline(PhotoEvaluationPipeline):

    def __init__(
        self,
        outcome: PipelineOutcome | None = None,
        error: Exception | None = None,
    ) -> None:
        self._outcome = outcome
        self._error = error
        self.calls: list[tuple[str, str, list[PhotoToEvaluate]]] = []

    def run(
        self, batch_id: str, anchor: str, photos: list[PhotoToEvaluate]
    ) -> PipelineOutcome:
        self.calls.append((batch_id, anchor, photos))
        if self._error is not None:
            raise self._error
        assert self._outcome is not None
        return self._outcome


class FakePhotoStorage(PhotoStorage):
    def __init__(self) -> None:
        self.saved: list[tuple[str, str, bytes]] = []
        self.deleted_batches: list[str] = []

    def save(self, batch_id: str, file_name: str, content: bytes) -> str:
        self.saved.append((batch_id, file_name, content))
        return f"/fake/{batch_id}/{file_name}"

    def delete_batch(self, batch_id: str) -> None:
        self.deleted_batches.append(batch_id)


class FakePhotusBClient(PhotusBClient):

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
