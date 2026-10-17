from __future__ import annotations

from domain.application.dtos.evaluation_batch_dto import BatchPhotoFile
from domain.application.exceptions.evaluation_batch_exceptions import PhotoNotFoundError
from domain.application.interfaces.evaluation_batch_repository import (
    EvaluationBatchRepository,
)
from domain.application.services.batch_access import load_owned_batch


class GetBatchPhotoFile:
    """Localiza o arquivo de uma foto do lote para exibição (UC08), só para o proprietário."""

    def __init__(self, batch_repository: EvaluationBatchRepository) -> None:
        self._batch_repository = batch_repository

    def execute(self, batch_id: str, photo_id: str, user_id: str) -> BatchPhotoFile:
        batch = load_owned_batch(self._batch_repository, batch_id, user_id)
        for photo in self._batch_repository.list_photos(batch.id):
            if photo.id == photo_id:
                return BatchPhotoFile(file_name=photo.file_name, file_path=photo.file_path)
        raise PhotoNotFoundError(photo_id)
