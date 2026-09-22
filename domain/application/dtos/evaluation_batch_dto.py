"""
DTOs de request/response para os use cases de EvaluationBatch (UC04–UC05).

São contratos de entrada/saída — não têm comportamento. Mantêm os use
cases desacoplados do formato exato de request usado na camada de API
(FastAPI/multipart, se for essa a escolha do front de acesso).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

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
