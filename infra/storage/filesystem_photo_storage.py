from __future__ import annotations

import shutil
from pathlib import Path

from domain.application.interfaces.photo_storage import PhotoStorage


class FilesystemPhotoStorage(PhotoStorage):
    def __init__(self, base_dir: str) -> None:
        self._base_dir = Path(base_dir)

    def save(self, batch_id: str, file_name: str, content: bytes) -> str:
        destination_dir = self._base_dir / batch_id
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination_path = destination_dir / file_name
        destination_path.write_bytes(content)
        return str(destination_path)

    def delete_batch(self, batch_id: str) -> None:
        target = (self._base_dir / batch_id).resolve()
        # Defesa em profundidade: batch_id vem do banco (uuid), mas nunca
        # apagamos nada fora do diretório de uploads.
        if self._base_dir.resolve() not in target.parents:
            return
        shutil.rmtree(target, ignore_errors=True)
