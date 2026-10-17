
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from domain.entities.evaluated_photo import PhotoEvaluationStatus
from domain.entities.evaluation_batch import BatchStatus, ClassificationRoute

# ---------------------------------------------------------------------------
# UC04 — Enviar Descrição + Fotografias
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PhotoUploadRequest:
    file_name: str
    content: bytes


@dataclass(frozen=True)
class SubmitBatchRequest:
    user_id: str
    input_text: str
    photos: list[PhotoUploadRequest]


@dataclass(frozen=True)
class SubmitBatchResponse:
    id: str
    user_id: str
    input_text: str
    status: BatchStatus
    classified_anchor: str | None
    classification_route: ClassificationRoute | None
    created_at: datetime


# ---------------------------------------------------------------------------
# UC05 — Classificar Âncora Semântica (Photus B)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ClassifyAnchorRequest:
    batch_id: str
    input_text: str


@dataclass(frozen=True)
class ClassifyAnchorResponse:
    batch_id: str
    status: BatchStatus
    classified_anchor: str | None
    classification_route: ClassificationRoute | None


# ---------------------------------------------------------------------------
# UC06 — Avaliar Fotografias (Photus A)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvaluatePhotosRequest:
    batch_id: str


@dataclass(frozen=True)
class EvaluatePhotosResponse:
    batch_id: str
    status: BatchStatus
    evaluated_photos: int  # fotos que receberam um status do engine (inclui `erro` por foto)
    thresholds_file: str | None


@dataclass(frozen=True)
class EvaluatedPhotoDetail:
    id: str
    file_name: str
    evaluation_status: PhotoEvaluationStatus
    final_score: float | None
    metrics_json: dict | None  # payload estruturado (RF10); `metrics_json` no banco é Text
    is_top3: bool


@dataclass(frozen=True)
class BatchDetailResponse:
    id: str
    user_id: str
    input_text: str
    status: BatchStatus
    classified_anchor: str | None
    classification_route: ClassificationRoute | None
    created_at: datetime
    thresholds_file: str | None
    total_photos: int
    evaluated_photos: int
    # UC09 — a frase original está no singular? (o front só destaca o Top 3 se sim)
    is_singular: bool
    photos: list[EvaluatedPhotoDetail]


# ---------------------------------------------------------------------------
# UC07 — Consultar Histórico / UC10 — Excluir Lote / foto do lote
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BatchSummary:
    id: str
    input_text: str
    status: BatchStatus
    classified_anchor: str | None
    classification_route: ClassificationRoute | None
    created_at: datetime
    total_photos: int
    is_singular: bool


@dataclass(frozen=True)
class BatchPhotoFile:
    file_name: str
    file_path: str
