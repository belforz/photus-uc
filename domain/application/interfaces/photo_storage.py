"""
Port de armazenamento de arquivos de fotografia (UC04).

Decisão já tomada (fora deste esqueleto): implementação concreta em
infra/storage/ persistindo em disco local. Este arquivo define só o
contrato que o use case depende.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class PhotoStorage(ABC):
    @abstractmethod
    def save(self, batch_id: str, file_name: str, content: bytes) -> str:
        """Persiste o conteúdo e retorna o caminho onde foi salvo."""
        raise NotImplementedError
