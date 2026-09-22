"""
Exceções de domínio para os use cases de EvaluationBatch (UC04–UC05).

Ficam na camada de aplicação para que a camada de API (FastAPI, por
exemplo) possa mapeá-las para status HTTP sem os use cases precisarem
saber o que é HTTP.
"""

from __future__ import annotations

PHOTO_LIMIT = 20


class EvaluationBatchError(Exception):
    """Base para todas as exceções de domínio de EvaluationBatch."""


class PhotoLimitExceededError(EvaluationBatchError):
    """UC04 — fluxo alternativo A1: mais de 20 fotografias anexadas."""

    def __init__(self, quantity: int, limit: int = PHOTO_LIMIT) -> None:
        super().__init__(f"Limite de {limit} fotografias excedido: {quantity} enviadas.")
        self.quantity = quantity
        self.limit = limit


class NoPhotosAttachedError(EvaluationBatchError):
    """UC04 — fluxo alternativo A2: nenhuma fotografia anexada."""


class PhotusBUnavailableError(EvaluationBatchError):
    """UC05 — fluxo alternativo A1: API do Photus B indisponível ou timeout.

    Levantada pela implementação concreta de PhotusBClient (infra/) e
    tratada dentro do use case ClassifySemanticAnchor (RNF06) — não
    deve escapar para a camada de API como um erro 5xx: o lote é
    marcado com status `erro` e o fluxo do usuário segue normalmente.
    """
