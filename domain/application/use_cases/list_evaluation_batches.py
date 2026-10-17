from __future__ import annotations

from domain.application.dtos.evaluation_batch_dto import BatchSummary
from domain.application.interfaces.evaluation_batch_repository import (
    EvaluationBatchRepository,
)
from domain.application.services.phrase_number import is_singular


class ListEvaluationBatches:
    """UC07 — histórico de lotes do usuário autenticado (RF12), isolado por proprietário (RF14)."""

    def __init__(self, batch_repository: EvaluationBatchRepository) -> None:
        self._batch_repository = batch_repository

    def execute(self, user_id: str) -> list[BatchSummary]:
        batches = self._batch_repository.list_by_user(user_id)
        counts = self._batch_repository.count_photos([b.id for b in batches])
        return [
            BatchSummary(
                id=b.id,
                input_text=b.input_text,
                status=b.status,
                classified_anchor=b.classified_anchor,
                classification_route=b.classification_route,
                created_at=b.created_at,
                total_photos=counts.get(b.id, 0),
                is_singular=is_singular(b.input_text),
            )
            for b in batches
        ]
