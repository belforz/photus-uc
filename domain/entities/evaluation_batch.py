
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class BatchStatus(str, Enum):
    PROCESSING = "em_processamento"
    COMPLETED = "concluido"  # UC06 — todas as fotos tiveram o engine executado
    ERROR = "erro"


class ClassificationRoute(str, Enum):
    TECHNICAL = "tecnico"
    FAST_TRACK = "fast_track"
    FALLBACK = "fallback"


@dataclass
class EvaluationBatch:
    id: str | None
    user_id: str
    input_text: str
    status: BatchStatus
    classified_anchor: str | None
    classification_route: ClassificationRoute | None
    created_at: datetime
