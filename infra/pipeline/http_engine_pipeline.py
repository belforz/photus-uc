
from __future__ import annotations

import mimetypes
from pathlib import Path

import httpx

from domain.application.exceptions.evaluation_batch_exceptions import EvaluationEngineError
from domain.application.interfaces.photo_evaluation_pipeline import (
    PhotoEvaluationPipeline,
    PhotoEvaluationResult,
    PhotoToEvaluate,
    PipelineOutcome,
)
from domain.entities.evaluated_photo import PhotoEvaluationStatus
from infra.pipeline.status_mapping import build_result


class HttpPhotoEvaluationPipeline(PhotoEvaluationPipeline):
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 600.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    def run(
        self, batch_id: str, anchor: str, photos: list[PhotoToEvaluate]
    ) -> PipelineOutcome:
        files = []
        for photo in photos:
            path = Path(photo.file_path)
            if not path.is_file():
                continue
            mime = mimetypes.guess_type(photo.file_name)[0] or "application/octet-stream"
            files.append(("photos", (photo.file_name, path.read_bytes(), mime)))
        if not files:
            raise EvaluationEngineError("Nenhuma fotografia do lote existe em disco.")

        try:
            with httpx.Client(transport=self._transport, timeout=self._timeout_seconds) as client:
                response = client.post(
                    f"{self._base_url}/v1/evaluate",
                    data={"batch_id": batch_id, "anchor": anchor},
                    files=files,
                )
        except httpx.HTTPError as exc:  # conexão recusada, DNS, timeout...
            raise EvaluationEngineError(
                f"photus-engine indisponível em {self._base_url}: {exc!r}"
            ) from exc

        if response.status_code != 200:
            raise _engine_error(response)

        body = response.json()
        return PipelineOutcome(
            results=[_to_result(item) for item in body.get("results", [])],
            thresholds_file=body["thresholds_file"],
            thresholds_source=body["thresholds_source"],
        )


def _to_result(item: dict) -> PhotoEvaluationResult:
    return build_result(
        item["file_name"],
        item.get("status"),
        item.get("final_score"),
        item.get("metrics"),
        item.get("face_metrics"),
        item.get("details"),
    )


def _engine_error(response: httpx.Response) -> EvaluationEngineError:
    try:
        body = response.json()
    except ValueError:
        body = {}
    detail = body.get("detail") if isinstance(body, dict) else None
    partial = [
        _to_result(item)
        for item in (body.get("partial_results", []) if isinstance(body, dict) else [])
    ]
    return EvaluationEngineError(
        f"photus-engine respondeu HTTP {response.status_code}: {detail or response.text[:300]}",
        partial_results=[r for r in partial if r.status != PhotoEvaluationStatus.ERROR],
    )
