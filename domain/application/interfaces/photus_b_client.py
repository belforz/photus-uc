
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class SemanticClassification:

    anchor: str
    technical: bool
    used_fallback: bool
    confidence: float


class PhotusBClient(ABC):
    @abstractmethod
    def classify_text(self, text: str) -> SemanticClassification:
        raise NotImplementedError
