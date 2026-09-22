"""
UC04 — Enviar Descrição + Fotografias.

Ator: Usuário Leigo / Fotógrafo (autenticado).
RFs relacionados: RF03, RF07, RF09.

Pré-condição: usuário autenticado (usuario_id vem de um token válido,
já decodificado antes deste use case ser chamado).
Fluxo principal:
    1. Usuário informa a descrição textual da estética desejada.
    2. Anexa até 20 fotografias.
    3. Sistema cria um registro em EvaluationBatch com status
       `em_processamento` e persiste as fotografias anexadas.
    4. Sistema aciona UC05 (ClassifySemanticAnchor) — relação
       <<include>>.
Fluxo alternativo A1: mais de 20 fotografias -> PhotoLimitExceededError.
Fluxo alternativo A2: nenhuma fotografia anexada -> NoPhotosAttachedError.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from domain.application.dtos.evaluation_batch_dto import (
    ClassifyAnchorRequest,
    SubmitBatchRequest,
    SubmitBatchResponse,
)
from domain.application.exceptions.evaluation_batch_exceptions import (
    PHOTO_LIMIT,
    NoPhotosAttachedError,
    PhotoLimitExceededError,
)
from domain.application.interfaces.evaluation_batch_repository import (
    EvaluationBatchRepository,
)
from domain.application.interfaces.photo_storage import PhotoStorage
from domain.application.use_cases.classify_semantic_anchor import ClassifySemanticAnchor
from domain.entities.evaluated_photo import EvaluatedPhoto, PhotoEvaluationStatus
from domain.entities.evaluation_batch import BatchStatus, EvaluationBatch


class SubmitEvaluationBatch:
    def __init__(
        self,
        batch_repository: EvaluationBatchRepository,
        photo_storage: PhotoStorage,
        classify_semantic_anchor: ClassifySemanticAnchor,
    ) -> None:
        self._batch_repository = batch_repository
        self._photo_storage = photo_storage
        self._classify_semantic_anchor = classify_semantic_anchor

    def execute(self, request: SubmitBatchRequest) -> SubmitBatchResponse:
        if len(request.photos) == 0:
            raise NoPhotosAttachedError()
        if len(request.photos) > PHOTO_LIMIT:
            raise PhotoLimitExceededError(len(request.photos))

        now = datetime.now(UTC)
        batch = EvaluationBatch(
            id=str(uuid.uuid4()),
            user_id=request.user_id,
            input_text=request.input_text,
            status=BatchStatus.PROCESSING,
            classified_anchor=None,
            classification_route=None,
            created_at=now,
        )
        created_batch = self._batch_repository.create(batch)

        photos = [
            EvaluatedPhoto(
                id=str(uuid.uuid4()),
                batch_id=created_batch.id,
                file_name=photo.file_name,
                file_path=self._photo_storage.save(
                    created_batch.id, photo.file_name, photo.content
                ),
                evaluation_status=PhotoEvaluationStatus.PENDING,
                created_at=now,
            )
            for photo in request.photos
        ]
        self._batch_repository.add_photos(photos)

        classification = self._classify_semantic_anchor.execute(
            ClassifyAnchorRequest(
                batch_id=created_batch.id, input_text=created_batch.input_text
            )
        )

        return SubmitBatchResponse(
            id=created_batch.id,
            user_id=created_batch.user_id,
            input_text=created_batch.input_text,
            status=classification.status,
            classified_anchor=classification.classified_anchor,
            classification_route=classification.classification_route,
            created_at=created_batch.created_at,
        )
