"""
Port de integração com o Photus B — serviço de roteamento semântico
(UC05). Decisão já tomada (fora deste esqueleto): implementação
concreta em infra/clients/ chamando a API HTTP do Photus B
(`POST /v1/categorize`). Este arquivo define só o contrato.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class SemanticClassification:
    """Resultado bruto da classificação semântica, direto do Photus B.

    `anchor` é o `category_code` já normalizado em slug pelo Photus B
    (ex.: "sublime", "tecnico") — a tradução/validação contra o
    vocabulário conhecido de âncoras (RF16) é responsabilidade do
    módulo `anchor_translator`, não deste client.
    """

    anchor: str
    technical: bool
    used_fallback: bool
    confidence: float


class PhotusBClient(ABC):
    @abstractmethod
    def classify_text(self, text: str) -> SemanticClassification:
        """Levanta PhotusBUnavailableError (UC05/A1) em caso de falha de
        rede ou timeout — não retorna um resultado parcial/inválido."""
        raise NotImplementedError
