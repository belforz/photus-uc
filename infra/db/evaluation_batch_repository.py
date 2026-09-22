from __future__ import annotations

from sqlalchemy.orm import Session

from domain.application.interfaces.evaluation_batch_repository import (
    EvaluationBatchRepository,
)
from domain.entities.evaluated_photo import EvaluatedPhoto, PhotoEvaluationStatus
from domain.entities.evaluation_batch import BatchStatus, ClassificationRoute, EvaluationBatch
from infra.db.models import EvaluatedPhotoModel, EvaluationBatchModel


class SQLAlchemyEvaluationBatchRepository(EvaluationBatchRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, batch: EvaluationBatch) -> EvaluationBatch:
        model = EvaluationBatchModel(
            id=batch.id,
            user_id=batch.user_id,
            input_text=batch.input_text,
            status=batch.status.value,
            classified_anchor=batch.classified_anchor,
            classification_route=(
                batch.classification_route.value if batch.classification_route else None
            ),
            created_at=batch.created_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def get_by_id(self, batch_id: str) -> EvaluationBatch | None:
        model = self._session.get(EvaluationBatchModel, batch_id)
        return _to_entity(model) if model is not None else None

    def add_photos(self, photos: list[EvaluatedPhoto]) -> list[EvaluatedPhoto]:
        models = [
            EvaluatedPhotoModel(
                id=photo.id,
                batch_id=photo.batch_id,
                file_name=photo.file_name,
                file_path=photo.file_path,
                evaluation_status=photo.evaluation_status.value,
                created_at=photo.created_at,
                final_score=photo.final_score,
                metrics_json=photo.metrics_json,
                is_top3=photo.is_top3,
            )
            for photo in photos
        ]
        self._session.add_all(models)
        self._session.commit()
        for model in models:
            self._session.refresh(model)
        return [_photo_to_entity(model) for model in models]

    def update_classification(self, batch: EvaluationBatch) -> EvaluationBatch:
        model = self._session.get(EvaluationBatchModel, batch.id)
        model.status = batch.status.value
        model.classified_anchor = batch.classified_anchor
        model.classification_route = (
            batch.classification_route.value if batch.classification_route else None
        )
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)


def _to_entity(model: EvaluationBatchModel) -> EvaluationBatch:
    return EvaluationBatch(
        id=model.id,
        user_id=model.user_id,
        input_text=model.input_text,
        status=BatchStatus(model.status),
        classified_anchor=model.classified_anchor,
        classification_route=(
            ClassificationRoute(model.classification_route)
            if model.classification_route
            else None
        ),
        created_at=model.created_at,
    )


def _photo_to_entity(model: EvaluatedPhotoModel) -> EvaluatedPhoto:
    return EvaluatedPhoto(
        id=model.id,
        batch_id=model.batch_id,
        file_name=model.file_name,
        file_path=model.file_path,
        evaluation_status=PhotoEvaluationStatus(model.evaluation_status),
        created_at=model.created_at,
        final_score=model.final_score,
        metrics_json=model.metrics_json,
        is_top3=model.is_top3,
    )
