"""
Entidade de domínio: EvaluationBatch (lote de avaliação).

Cobre RF03/RF04/RF05/RF06/RF09/RF16 da Proposta Técnica (Sprint 2).
Persistência real fica a cargo do adapter de repositório (infra/), não
desta classe.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class BatchStatus(str, Enum):
    PROCESSING = "em_processamento"
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
