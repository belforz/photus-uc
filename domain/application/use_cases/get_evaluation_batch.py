
from __future__ import annotations

import json

from domain.application.dtos.evaluation_batch_dto import (
    BatchDetailResponse,
    EvaluatedPhotoDetail,
)
from domain.application.exceptions.evaluation_batch_exceptions import BatchNotFoundError
from domain.application.interfaces.evaluation_batch_repository import (
    EvaluationBatchRepository,
)
from domain.entities.evaluated_photo import PhotoEvaluationStatus


class GetEvaluationBatch:
    def __init__(self, batch_repository: EvaluationBatchRepository) -> None:
        self._batch_repository = batch_repository

    def execute(self, batch_id: str, user_id: str) -> BatchDetailResponse:
        batch = self._batch_repository.get_by_id(batch_id)
        if batch is None or batch.user_id != user_id:
            raise BatchNotFoundError(batch_id)

        photos = self._batch_repository.list_photos(batch.id)
        details = [
            EvaluatedPhotoDetail(
                id=p.id,
                file_name=p.file_name,
                evaluation_status=p.evaluation_status,
                final_score=p.final_score,
                metrics_json=json.loads(p.metrics_json) if p.metrics_json else None,
                is_top3=p.is_top3,
            )
            for p in photos
        ]
        thresholds_file = next(
            (
                d.metrics_json.get("thresholds_file")
                for d in details
                if d.metrics_json and d.metrics_json.get("thresholds_file")
            ),
            None,
        )
        return BatchDetailResponse(
            id=batch.id,
            user_id=batch.user_id,
            input_text=batch.input_text,
            status=batch.status,
            classified_anchor=batch.classified_anchor,
            classification_route=batch.classification_route,
            created_at=batch.created_at,
            thresholds_file=thresholds_file,
            total_photos=len(details),
            evaluated_photos=sum(
                1 for d in details if d.evaluation_status != PhotoEvaluationStatus.PENDING
            ),
            photos=details,
        )
