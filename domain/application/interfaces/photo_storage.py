
from __future__ import annotations

from abc import ABC, abstractmethod


class PhotoStorage(ABC):
    @abstractmethod
    def save(self, batch_id: str, file_name: str, content: bytes) -> str:
        raise NotImplementedError
