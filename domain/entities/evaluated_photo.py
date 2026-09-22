"""
Entidade de domínio: EvaluatedPhoto (foto avaliada).

Cobre RF07/RF09 (Sprint 2 — anexo das fotografias do lote). Os campos
de avaliação técnica (final_score, metrics_json, is_top3) só são
preenchidos pelo UC06 (Sprint 3) — aqui nascem vazios/pendentes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class PhotoEvaluationStatus(str, Enum):
    PENDING = "pendente"
    APPROVED = "aprovado"
    REJECTED = "reprovado"


@dataclass
class EvaluatedPhoto:
    id: str | None
    batch_id: str
    file_name: str
    file_path: str
    evaluation_status: PhotoEvaluationStatus
    created_at: datetime
    final_score: float | None = None
    metrics_json: str | None = None
    is_top3: bool = False
