from __future__ import annotations

from domain.application.exceptions.evaluation_batch_exceptions import (
    BatchAccessDeniedError,
    BatchNotFoundError,
)
from domain.application.interfaces.evaluation_batch_repository import (
    EvaluationBatchRepository,
)
from domain.entities.evaluation_batch import EvaluationBatch


def load_owned_batch(
    repository: EvaluationBatchRepository, batch_id: str, user_id: str
) -> EvaluationBatch:
    """RF14 — isolamento por proprietário: 404 se não existe, 403 se é de outro usuário."""
    batch = repository.get_by_id(batch_id)
    if batch is None:
        raise BatchNotFoundError(batch_id)
    if batch.user_id != user_id:
        raise BatchAccessDeniedError(batch_id)
    return batch
