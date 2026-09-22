from __future__ import annotations

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
