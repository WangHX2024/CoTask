"""MinIO singleton + helpers."""
from __future__ import annotations

import logging
from datetime import timedelta
from urllib.parse import urlparse

from flask import current_app
from minio import Minio

log = logging.getLogger(__name__)

_internal_client: Minio | None = None
_public_client: Minio | None = None


def _parse_endpoint(raw: str) -> tuple[str, bool]:
    """Return (host:port, secure) from MINIO_ENDPOINT or MINIO_PUBLIC_ENDPOINT."""
    if "://" not in raw:
        raw = f"http://{raw}"
    parsed = urlparse(raw)
    host = parsed.netloc or parsed.path
    secure = parsed.scheme == "https"
    return host, secure


def _minio_kwargs(cfg: dict, endpoint_key: str) -> dict:
    host, secure = _parse_endpoint(cfg[endpoint_key])
    return {
        "endpoint": host,
        "access_key": cfg["MINIO_ACCESS_KEY"],
        "secret_key": cfg["MINIO_SECRET_KEY"],
        "secure": secure,
        # Avoid live bucket-location lookup (public host is unreachable from api container)
        "region": "us-east-1",
    }


def get_client() -> Minio:
    """Internal client (Docker network hostname) for bucket ops."""
    global _internal_client
    if _internal_client is None:
        cfg = current_app.config
        _internal_client = Minio(**_minio_kwargs(cfg, "MINIO_ENDPOINT"))
    return _internal_client


def get_public_client() -> Minio:
    """Client used for browser-facing presigned URLs."""
    global _public_client
    if _public_client is None:
        cfg = current_app.config
        key = "MINIO_PUBLIC_ENDPOINT" if cfg.get("MINIO_PUBLIC_ENDPOINT") else "MINIO_ENDPOINT"
        _public_client = Minio(**_minio_kwargs(cfg, key))
    return _public_client


def ensure_bucket():
    cli = get_client()
    bucket = current_app.config["MINIO_BUCKET"]
    if not cli.bucket_exists(bucket):
        cli.make_bucket(bucket)
    return bucket


def presign_put(key: str, content_type: str | None = None, expires_minutes: int = 10) -> str:
    _ = content_type  # minio 7.x presign does not bind Content-Type
    cli = get_public_client()
    bucket = ensure_bucket()
    return cli.presigned_put_object(
        bucket,
        key,
        expires=timedelta(minutes=expires_minutes),
    )


def presign_get(key: str, expires_minutes: int = 60) -> str:
    cli = get_public_client()
    bucket = ensure_bucket()
    return cli.presigned_get_object(bucket, key, expires=timedelta(minutes=expires_minutes))
