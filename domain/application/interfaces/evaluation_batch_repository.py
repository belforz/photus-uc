
from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.evaluated_photo import EvaluatedPhoto
from domain.entities.evaluation_batch import EvaluationBatch


class EvaluationBatchRepository(ABC):
    @abstractmethod
    def create(self, batch: EvaluationBatch) -> EvaluationBatch:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, batch_id: str) -> EvaluationBatch | None:
        raise NotImplementedError

    @abstractmethod
    def add_photos(self, photos: list[EvaluatedPhoto]) -> list[EvaluatedPhoto]:
        raise NotImplementedError

    @abstractmethod
    def update_classification(self, batch: EvaluationBatch) -> EvaluationBatch:
        raise NotImplementedError

    @abstractmethod
    def list_photos(self, batch_id: str) -> list[EvaluatedPhoto]:
        raise NotImplementedError

    @abstractmethod
    def update_photo_evaluations(self, photos: list[EvaluatedPhoto]) -> list[EvaluatedPhoto]:
        raise NotImplementedError

    @abstractmethod
    def update_status(self, batch: EvaluationBatch) -> EvaluationBatch:
        raise NotImplementedError

    @abstractmethod
    def list_by_user(self, user_id: str) -> list[EvaluationBatch]:
        """Lotes do usuário, do mais recente para o mais antigo (UC07)."""
        raise NotImplementedError

    @abstractmethod
    def count_photos(self, batch_ids: list[str]) -> dict[str, int]:
        raise NotImplementedError

    @abstractmethod
    def delete(self, batch_id: str) -> None:
        """Remove o lote e, em cascata, suas fotos avaliadas (UC10 / RF13)."""
        raise NotImplementedError
