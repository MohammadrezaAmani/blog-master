import os
from datetime import timedelta

from fastapi import HTTPException
from minio import Minio
from src.config.settings import (
    AWS_ACCESS_KEY,
    AWS_SECRET_ACCESS_KEY,
    CACHE_TTL,
    MINIO_BASE_BUCKETS,
    MINIO_KWARGS,
    MINIO_URI,
)
from src.helper.redis.cache import cache, cached

minio_client = Minio(
    endpoint=MINIO_URI,
    access_key=AWS_ACCESS_KEY,
    secret_key=AWS_SECRET_ACCESS_KEY,
    secure=False,
    **(MINIO_KWARGS or {}),
)


async def ensure_bucket_exists(
    bucket_name: str | list[str] = MINIO_BASE_BUCKETS,
    minio_client: Minio = minio_client,
):
    if isinstance(bucket_name, str):
        bucket_name = [bucket_name]
    for bucket in bucket_name:
        if not minio_client.bucket_exists(bucket):
            minio_client.make_bucket(bucket)


async def upload_to_minio(
    temp_file_path: str,
    file_name: str,
    content_type: str = "Application/octet-stream",
    bucket_name: str = MINIO_BASE_BUCKETS[0],
):
    try:
        minio_client.fput_object(
            bucket_name, file_name, temp_file_path, content_type=content_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to upload to MinIO: {str(e)}"
        )
    finally:
        os.remove(temp_file_path)


@cached(ttl=CACHE_TTL, cache=cache)
async def generate_presigned_url(
    file_name: str | list[str], bucket_name: str = MINIO_BASE_BUCKETS[0]
) -> str | list[str]:
    if isinstance(file_name, list):
        return [await generate_presigned_url(name) for name in file_name]
    try:
        return minio_client.presigned_get_object(
            bucket_name, file_name, expires=timedelta(seconds=CACHE_TTL + 1)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate URL: {str(e)}")
