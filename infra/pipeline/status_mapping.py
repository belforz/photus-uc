from __future__ import annotations

import unicodedata

from domain.application.interfaces.photo_evaluation_pipeline import PhotoEvaluationResult
from domain.entities.evaluated_photo import PhotoEvaluationStatus

_STATUS_MAP = {
    "aprovado": PhotoEvaluationStatus.APPROVED,
    "indefinido": PhotoEvaluationStatus.UNDEFINED,
    "reprovado": PhotoEvaluationStatus.REJECTED,
    "revisao_humana": PhotoEvaluationStatus.HUMAN_REVIEW,
    "error": PhotoEvaluationStatus.ERROR,
}


def normalize_status(raw: str | None) -> PhotoEvaluationStatus | None:
    if not raw:
        return None
    ascii_only = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode()
    return _STATUS_MAP.get(ascii_only.strip().lower().replace(" ", "_"))


def build_result(
    file_name: str,
    raw_status: str | None,
    final_score: float | None,
    metrics: dict | None,
    face_metrics: dict | None,
    details: str | None,
) -> PhotoEvaluationResult:
    status = normalize_status(raw_status)
    if status is None:
        status = PhotoEvaluationStatus.ERROR
        details = f"Status desconhecido do engine: {raw_status!r}. {details or ''}".strip()
    return PhotoEvaluationResult(
        file_name=file_name,
        status=status,
        final_score=float(final_score) if final_score is not None else None,
        metrics=metrics or {},
        face_metrics=face_metrics,
        details=details,
    )
