from __future__ import annotations

import httpx

from domain.application.exceptions.evaluation_batch_exceptions import (
    PhotusBUnavailableError,
)
from domain.application.interfaces.photus_b_client import PhotusBClient, SemanticClassification


class HttpPhotusBClient(PhotusBClient):
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def classify_text(self, text: str) -> SemanticClassification:
        try:
            response = httpx.post(
                f"{self._base_url}/v1/categorize",
                json={"text": text},
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise PhotusBUnavailableError(str(exc)) from exc

        body = response.json()
        return SemanticClassification(
            anchor=body["category_code"],
            technical=body["technical"],
            used_fallback=bool(body.get("used_fallback", False)),
            confidence=body["confidence"],
        )
