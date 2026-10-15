
from __future__ import annotations

import random
import struct
import zlib
from pathlib import Path


def _chunk(tag: bytes, data: bytes) -> bytes:
    body = tag + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))


def write_rgb_png(path: Path, width: int, height: int, row_fn) -> Path:
    raw = b"".join(b"\x00" + row_fn(y) for y in range(height))
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(raw, 6))
        + _chunk(b"IEND", b"")
    )
    path.write_bytes(png)
    return path


def write_underexposed_png(path: Path, width: int = 800, height: int = 600) -> Path:
    rng = random.Random(7)
    return write_rgb_png(
        path, width, height, lambda _y: bytes(b & 3 for b in rng.randbytes(width * 3))
    )


def write_black_png(path: Path, width: int = 800, height: int = 600) -> Path:
    return write_rgb_png(path, width, height, lambda _y: bytes(width * 3))


def write_overexposed_png(path: Path, width: int = 800, height: int = 600) -> Path:
    return write_rgb_png(path, width, height, lambda _y: b"\xff" * (width * 3))


def write_flat_gradient_png(path: Path, width: int = 800, height: int = 600) -> Path:
    def row(y: int) -> bytes:
        return bytes(((x * 200) // width + 20) for x in range(width) for _ in range(3))

    return write_rgb_png(path, width, height, row)
