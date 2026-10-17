
from __future__ import annotations

PHOTO_LIMIT = 20


class EvaluationBatchError(Exception):
    pass


class PhotoLimitExceededError(EvaluationBatchError):

    def __init__(self, quantity: int, limit: int = PHOTO_LIMIT) -> None:
        super().__init__(f"Limite de {limit} fotografias excedido: {quantity} enviadas.")
        self.quantity = quantity
        self.limit = limit


class NoPhotosAttachedError(EvaluationBatchError):
    pass


class BatchNotFoundError(EvaluationBatchError):
    pass


class AnchorNotClassifiedError(EvaluationBatchError):
    pass


class EvaluationEngineError(EvaluationBatchError):

    def __init__(self, message: str, partial_results: list | None = None) -> None:
        super().__init__(message)
        self.partial_results = partial_results or []


class PhotusBUnavailableError(EvaluationBatchError):
    pass


class BatchAccessDeniedError(EvaluationBatchError):
    """RF14 — o lote existe, mas pertence a outro usuário."""


class PhotoNotFoundError(EvaluationBatchError):
    pass
