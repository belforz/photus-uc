from __future__ import annotations

from domain.application.interfaces.evaluation_batch_repository import (
    EvaluationBatchRepository,
)
from domain.application.interfaces.photo_storage import PhotoStorage
from domain.application.services.batch_access import load_owned_batch


class DeleteEvaluationBatch:
    """UC10 — exclui o lote, as fotos avaliadas (cascata, RF13) e os arquivos enviados."""

    def __init__(
        self, batch_repository: EvaluationBatchRepository, photo_storage: PhotoStorage
    ) -> None:
        self._batch_repository = batch_repository
        self._photo_storage = photo_storage

    def execute(self, batch_id: str, user_id: str) -> None:
        batch = load_owned_batch(self._batch_repository, batch_id, user_id)
        self._batch_repository.delete(batch.id)
        self._photo_storage.delete_batch(batch.id)
