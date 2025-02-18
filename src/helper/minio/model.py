import os
import uuid
from datetime import datetime, timezone
from typing import List, Tuple

from aiofiles import open as aio_open
from fastapi import UploadFile
from tortoise import fields

from src.base import BaseModel
from src.config.settings import MINIO_BASE_BUCKETS
from src.helper.minio.controller import generate_presigned_url, upload_to_minio


class File(BaseModel):
    url = fields.CharField(max_length=255, unique=True)
    name = fields.CharField(max_length=255, default="")
    description = fields.TextField(null=True)
    user = fields.ForeignKeyField(
        "models.User", related_name="files", on_delete=fields.CASCADE, null=True
    )
    size = fields.BigIntField(null=True)
    tags = fields.JSONField(null=True)
    content_type = fields.CharField(max_length=255, default="Application/octet-stream")
    bucket_name = fields.CharField(max_length=255, null=True)

    @staticmethod
    async def upload(
        file: UploadFile | list[UploadFile],
        user,
        bucket_name: str = MINIO_BASE_BUCKETS[0],
        category: str = "files",
    ) -> Tuple["File", str] | List[Tuple["File", str]]:
        if isinstance(file, list):
            return [await File.upload(i, user, bucket_name, category) for i in file]
        current_date = datetime.now(tz=timezone.utc).strftime("%Y/%m/%d")
        file_id = str(uuid.uuid4())
        file_name = (
            f"{user.username}/{category}/{current_date}/{file_id}_{file.filename}"
        )
        os.makedirs("./tmp", exist_ok=True)
        temp_file_path = f"./tmp/{uuid.uuid4()}_{file.filename}"

        async with aio_open(temp_file_path, "wb") as temp_file:
            while chunk := await file.read(1024 * 1024):
                await temp_file.write(chunk)

        await upload_to_minio(temp_file_path, file_name, file.content_type)
        file_url = await generate_presigned_url(file_name)
        obj = await File.create(
            name=file.filename,
            url=file_name,
            description="",
            content_type=file.content_type,
            user_id=user.pk,
            bucket_name=bucket_name,
            size=file.size,
        )
        return obj, file_url

    async def download(self) -> str:
        return await generate_presigned_url(self.url, self.bucket_name)
