from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from domain.entities.evaluated_photo import PhotoEvaluationStatus
from domain.entities.evaluation_batch import BatchStatus, ClassificationRoute


class BatchPublic(BaseModel):
    id: str
    user_id: str
    input_text: str
    status: BatchStatus
    classified_anchor: str | None
    classification_route: ClassificationRoute | None
    created_at: datetime


class EvaluatedPhotoPublic(BaseModel):
    id: str
    file_name: str
    evaluation_status: PhotoEvaluationStatus
    final_score: float | None
    # Payload estruturado do Photus A (RF10): metrics, face_metrics, details,
    # thresholds_file/source. Objeto JSON (no banco é Text serializado).
    metrics_json: dict[str, Any] | None
    is_top3: bool


class BatchDetailPublic(BatchPublic):
    thresholds_file: str | None
    total_photos: int
    evaluated_photos: int
    photos: list[EvaluatedPhotoPublic]
