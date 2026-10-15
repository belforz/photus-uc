
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class PhotoEvaluationStatus(str, Enum):
    PENDING = "pendente"
    APPROVED = "aprovado"
    UNDEFINED = "indefinido"
    REJECTED = "reprovado"
    HUMAN_REVIEW = "revisao_humana"
    # Extensão além dos 4 status da spec (Aprovado/Indefinido/Reprovado/Revisão
    # Humana): o engine falhou para esta foto específica (ex.: imagem ilegível).
    # O registro é preservado e o lote segue (Figma Sprint 3: "Registro preservado").
    ERROR = "erro"


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
