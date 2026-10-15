from __future__ import annotations

import logging
from collections.abc import Callable

from sqlalchemy.orm import Session

from domain.application.dtos.evaluation_batch_dto import EvaluatePhotosRequest
from domain.application.interfaces.photo_evaluation_pipeline import PhotoEvaluationPipeline
from domain.application.use_cases.evaluate_photos import EvaluatePhotos
from domain.entities.evaluation_batch import BatchStatus
from infra.db.evaluation_batch_repository import SQLAlchemyEvaluationBatchRepository

logger = logging.getLogger(__name__)

EvaluationJob = Callable[[str], None]


class SessionEvaluationJob:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        pipeline: PhotoEvaluationPipeline,
    ) -> None:
        self._session_factory = session_factory
        self._pipeline = pipeline

    def __call__(self, batch_id: str) -> None:
        session = self._session_factory()
        try:
            repo = SQLAlchemyEvaluationBatchRepository(session)
            try:
                EvaluatePhotos(repo, self._pipeline).execute(EvaluatePhotosRequest(batch_id))
            except Exception:
                logger.exception("UC06 falhou inesperadamente para o lote %s", batch_id)
                session.rollback()
                batch = repo.get_by_id(batch_id)
                if batch is not None and batch.status == BatchStatus.PROCESSING:
                    batch.status = BatchStatus.ERROR
                    repo.update_status(batch)
        finally:
            session.close()
