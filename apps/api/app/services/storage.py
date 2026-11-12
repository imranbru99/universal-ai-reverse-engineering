from __future__ import annotations

import hashlib
from pathlib import Path

from app.config import get_settings


def _artifact_root() -> Path:
    settings = get_settings()
    root = Path(settings.export_dir) / "artifacts"
    root.mkdir(parents=True, exist_ok=True)
    return root


def put_bytes(key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    # Local filesystem object store (S3-compatible wiring deferred when registry access allows MinIO).
    path = _artifact_root() / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    _ = content_type
    return key


def put_file(key: str, path: Path, content_type: str = "application/octet-stream") -> str:
    return put_bytes(key, path.read_bytes(), content_type)


def get_bytes(key: str) -> bytes:
    path = _artifact_root() / key
    if not path.exists():
        # also check export mirror filenames
        mirror = local_export_path(Path(key).name)
        if mirror.exists():
            return mirror.read_bytes()
        raise FileNotFoundError(key)
    return path.read_bytes()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def local_export_path(filename: str) -> Path:
    settings = get_settings()
    root = Path(settings.export_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root / filename
