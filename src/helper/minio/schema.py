import base64
import io
from typing import Optional

from pydantic import Field

from src.base.scheme import BaseCreateScheme, BaseResponseScheme
from src.config.settings import MINIO_BASE_BUCKETS
from src.helper.minio.model import File


class FileCreateScheme(BaseCreateScheme):
    link: str | None = None
    name: str = Field("", max_length=255)
    description: str | None = None
    user_id: int | None = None
    tags: Optional[dict] = None
    content_type: str | None = None
    size: int | None = None

    @staticmethod
    async def from_tortoise_orm(
        cls, obj, many=False, fields=None, exclude=None, extra_fields=None, m2m=None
    ) -> "FileCreateScheme":
        result = []
        if many:
            for i in obj:
                data = await cls.from_tortoise_orm(
                    cls, i, False, fields, exclude, extra_fields, m2m
                )

                result.append(data)
            return result
        else:
            result = await super().from_tortoise_orm(
                cls, obj, False, fields, exclude, extra_fields, m2m
            )

            result.link = await obj.download()
        return result

    async def create(
        self, user_id: int, bucket_name: str = MINIO_BASE_BUCKETS[0], url: str = None
    ):
        return await File.upload(
            bucket_name=bucket_name,
            name=self.name,
            tags=self.tags,
            description=self.description,
            user_id=user_id,
            url=url,
        )

    @property
    def file(self):
        file_data = base64.b64decode(self.body)
        file_stream = io.BytesIO(file_data)
        file_stream.seek(0)
        return file_stream


class FileResponseScheme(BaseResponseScheme, FileCreateScheme): ...
