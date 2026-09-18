from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from domain.entities.evaluation_batch import BatchStatus, ClassificationRoute


class BatchPublic(BaseModel):
    id: str
    user_id: str
    input_text: str
    status: BatchStatus
    classified_anchor: str | None
    classification_route: ClassificationRoute | None
    created_at: datetime
