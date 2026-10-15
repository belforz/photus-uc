
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal

from domain.entities.evaluated_photo import PhotoEvaluationStatus


@dataclass(frozen=True)
class PhotoToEvaluate:
    file_name: str
    file_path: str


@dataclass(frozen=True)
class PhotoEvaluationResult:

    file_name: str
    status: PhotoEvaluationStatus
    final_score: float | None
    metrics: dict = field(default_factory=dict)  # sharpness, edge_density, exposure_ratio...
    face_metrics: dict | None = None  # YuNet; None quando o engine não reportou
    details: str | None = None  # hard-rule aplicada / mensagem de erro por foto


@dataclass(frozen=True)
class PipelineOutcome:
    results: list[PhotoEvaluationResult]
    # Qual arquivo de thresholds o Photus A efetivamente usou (RF16/RNF04/RNF05).
    thresholds_file: str
    thresholds_source: Literal["specific", "global"]


class PhotoEvaluationPipeline(ABC):
    @abstractmethod
    def run(
        self, batch_id: str, anchor: str, photos: list[PhotoToEvaluate]
    ) -> PipelineOutcome:
        raise NotImplementedError
