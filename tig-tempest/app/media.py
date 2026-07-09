"""Object storage (MinIO / S3-compatible) — avatars + banners.

Uploaded images live in MinIO, not on the app's disk, so the app stays stateless.
We serve them back through the app's own /media/<key> route (portable: works in
local dev and on the box, no Caddy media rule needed). Adapted from freehold.
"""
import io
import os
import secrets

from minio import Minio

ENDPOINT = os.getenv("MINIO_ENDPOINT", "tempest-minio:9000")
ACCESS = os.getenv("MINIO_ROOT_USER", "tempest")
SECRET = os.getenv("MINIO_ROOT_PASSWORD", "tempest_dev")
BUCKET = os.getenv("MINIO_BUCKET", "tempest")

_client = Minio(ENDPOINT, access_key=ACCESS, secret_key=SECRET, secure=False)
_ready = False

EXT = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}


def _ensure() -> None:
    global _ready
    if _ready:
        return
    if not _client.bucket_exists(BUCKET):
        _client.make_bucket(BUCKET)
    _ready = True


def is_image(content_type: str | None) -> bool:
    return content_type in EXT


def save_image(data: bytes, content_type: str, prefix: str = "img") -> str:
    """Store bytes under prefix/<random>.<ext>; return the object key."""
    _ensure()
    key = f"{prefix}/{secrets.token_hex(12)}.{EXT.get(content_type, 'bin')}"
    _client.put_object(BUCKET, key, io.BytesIO(data), length=len(data), content_type=content_type)
    return key


def stream(key: str):
    """(iterator, content_type) for serving an object; iterator closes the conn."""
    obj = _client.get_object(BUCKET, key)
    content_type = obj.headers.get("Content-Type", "application/octet-stream")

    def _it():
        try:
            yield from obj.stream(32 * 1024)
        finally:
            obj.close()
            obj.release_conn()

    return _it(), content_type


def url(key: str | None) -> str:
    return f"/media/{key}" if key else ""
