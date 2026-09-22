"""
Port de persistência para EvaluationBatch e EvaluatedPhoto.

A implementação concreta (ex.: SQLAlchemy) vive em infra/ e é injetada
nos use cases — os use cases nunca importam uma implementação
concreta diretamente.
"""

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
        """Persiste status/classified_anchor/classification_route (UC05)."""
        raise NotImplementedError
