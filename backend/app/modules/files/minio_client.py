"""MinIO singleton + helpers."""
from __future__ import annotations

import logging
from datetime import timedelta

from flask import current_app
from minio import Minio

log = logging.getLogger(__name__)

_client: Minio | None = None


def get_client() -> Minio:
    global _client
    if _client is None:
        cfg = current_app.config
        _client = Minio(
            cfg["MINIO_ENDPOINT"],
            access_key=cfg["MINIO_ACCESS_KEY"],
            secret_key=cfg["MINIO_SECRET_KEY"],
            secure=bool(cfg.get("MINIO_SECURE")),
        )
    return _client


def ensure_bucket():
    cli = get_client()
    bucket = current_app.config["MINIO_BUCKET"]
    if not cli.bucket_exists(bucket):
        cli.make_bucket(bucket)
    return bucket


def presign_put(key: str, content_type: str | None = None, expires_minutes: int = 10) -> str:
    cli = get_client()
    bucket = ensure_bucket()
    return cli.presigned_put_object(bucket, key, expires=timedelta(minutes=expires_minutes))


def presign_get(key: str, expires_minutes: int = 60) -> str:
    cli = get_client()
    bucket = ensure_bucket()
    return cli.presigned_get_object(bucket, key, expires=timedelta(minutes=expires_minutes))
