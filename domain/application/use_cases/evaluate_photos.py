
from __future__ import annotations

import json
from dataclasses import replace

from domain.application.dtos.evaluation_batch_dto import (
    EvaluatePhotosRequest,
    EvaluatePhotosResponse,
)
from domain.application.exceptions.evaluation_batch_exceptions import (
    AnchorNotClassifiedError,
    BatchNotFoundError,
    EvaluationEngineError,
)
from domain.application.interfaces.evaluation_batch_repository import (
    EvaluationBatchRepository,
)
from domain.application.interfaces.photo_evaluation_pipeline import (
    PhotoEvaluationPipeline,
    PhotoEvaluationResult,
    PhotoToEvaluate,
)
from domain.entities.evaluated_photo import EvaluatedPhoto, PhotoEvaluationStatus
from domain.entities.evaluation_batch import BatchStatus


class EvaluatePhotos:
    def __init__(
        self,
        batch_repository: EvaluationBatchRepository,
        pipeline: PhotoEvaluationPipeline,
    ) -> None:
        self._batch_repository = batch_repository
        self._pipeline = pipeline

    def execute(self, request: EvaluatePhotosRequest) -> EvaluatePhotosResponse:
        batch = self._batch_repository.get_by_id(request.batch_id)
        if batch is None:
            raise BatchNotFoundError(request.batch_id)
        if batch.classified_anchor is None:
            raise AnchorNotClassifiedError(
                f"Lote {batch.id} não tem âncora classificada — UC05 deve rodar antes."
            )

        photos = self._batch_repository.list_photos(batch.id)
        to_evaluate = [PhotoToEvaluate(p.file_name, p.file_path) for p in photos]

        try:
            outcome = self._pipeline.run(batch.id, batch.classified_anchor, to_evaluate)
        except EvaluationEngineError as exc:
            # A2 — preserva o que o engine chegou a avaliar e marca o lote como erro.
            salvas = _apply_results(
                photos,
                exc.partial_results,
                pipeline_succeeded=False,
                thresholds_file=None,
                anchor=batch.classified_anchor,
            )
            self._batch_repository.update_photo_evaluations(salvas)
            batch.status = BatchStatus.ERROR
            self._batch_repository.update_status(batch)
            return EvaluatePhotosResponse(
                batch_id=batch.id,
                status=BatchStatus.ERROR,
                evaluated_photos=sum(
                    1 for p in salvas if p.evaluation_status != PhotoEvaluationStatus.PENDING
                ),
                thresholds_file=None,
            )

        avaliadas = _apply_results(
            photos,
            outcome.results,
            pipeline_succeeded=True,
            thresholds_file=outcome.thresholds_file,
            anchor=batch.classified_anchor,
            thresholds_source=outcome.thresholds_source,
        )
        self._batch_repository.update_photo_evaluations(avaliadas)
        batch.status = BatchStatus.COMPLETED
        self._batch_repository.update_status(batch)

        return EvaluatePhotosResponse(
            batch_id=batch.id,
            status=BatchStatus.COMPLETED,
            evaluated_photos=len(avaliadas),
            thresholds_file=outcome.thresholds_file,
        )


def _apply_results(
    photos: list[EvaluatedPhoto],
    results: list[PhotoEvaluationResult],
    *,
    pipeline_succeeded: bool,
    thresholds_file: str | None,
    anchor: str,
    thresholds_source: str | None = None,
) -> list[EvaluatedPhoto]:
    by_name = {r.file_name: r for r in results}
    out: list[EvaluatedPhoto] = []
    for photo in photos:
        result = by_name.get(photo.file_name)
        if result is None:
            if pipeline_succeeded:
                result = PhotoEvaluationResult(
                    file_name=photo.file_name,
                    status=PhotoEvaluationStatus.ERROR,
                    final_score=None,
                    details="Engine não retornou resultado para esta fotografia.",
                )
            else:
                out.append(photo)
                continue
        payload = {
            "anchor": anchor,
            "thresholds_file": thresholds_file,
            "thresholds_source": thresholds_source,
            "metrics": result.metrics,
            "face_metrics": result.face_metrics,
            "details": result.details,
        }
        out.append(
            replace(
                photo,
                evaluation_status=result.status,
                final_score=result.final_score,
                metrics_json=json.dumps(payload, ensure_ascii=False),
            )
        )
    return out
