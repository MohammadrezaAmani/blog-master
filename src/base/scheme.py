from datetime import datetime
from typing import Any, TypeVar

from pydantic import BaseModel
from tortoise import Model
from tortoise.queryset import QuerySet

from src.helper.utils import call

T = TypeVar("T")


class BaseCreateScheme(BaseModel):
    @staticmethod
    async def from_tortoise_orm(
        cls: T,
        obj: Model | list[Model],
        many=False,
        fields: list[str] | None = None,
        exclude: list[str] | None = None,
        extra_fields: list[str] | None = None,
        m2m: list[tuple[str, QuerySet]] | None = None,
    ) -> T:
        if many:
            return [await cls.from_tortoise_orm(cls, i) for i in obj]

        result = cls(
            **{
                key: obj.__dict__[key]
                for key in set(
                    (*(fields or obj.__dict__.keys()), *(extra_fields or []))
                )
                if (not key.startswith("_") or key in (extra_fields or []))
                and key not in (exclude or [])
            }
        )
        if m2m:
            for m in m2m or []:
                setattr(
                    result,
                    m[0],
                    await getattr(obj, m[1]).all().values_list("id", flat=True),
                )
        return result

    async def update_m2m(
        self, obj, m2m: list[tuple[str, list[int], Model]] | None = None
    ):
        if not m2m:
            return
        for m in m2m:
            await getattr(obj, m[0]).clear()
            await getattr(obj, m[0]).add(*(await m[2].filter(id__in=m[1] or [])))

    async def create(
        self,
        model: Model,
        serialize: bool = False,
        serializer=None,
        m2m: list[tuple[str, list[int], Model]] | None = None,
        exclude: list[str] | None = None,
        defaults: dict[str, Any] | None = None,
        **kwarg,
    ):
        exclude = exclude or []
        exclude.extend([i[0] for i in m2m or []])
        data = defaults or {}
        data.update(**self.model_dump(exclude_unset=True, exclude=exclude))
        data.update(**kwarg)
        obj = await model.create(**data)
        await self.update_m2m(obj, m2m)
        if serialize:
            return await call(
                (serializer or self.__class__).from_tortoise_orm,
                (serializer or self.__class__),
                obj,
                m2m=[(m[0], m[0]) for m in m2m or []],
            )
        return obj

    async def update(
        self,
        obj,
        serialize: bool = False,
        serializer=None,
        m2m: list[tuple[str, list[int], Model]] | None = None,
        exclude: list[str] | None = None,
        defaults: dict[str, Any] | None = None,
        **kwarg,
    ):
        exclude = exclude or []
        exclude.extend([i[0] for i in m2m or []])
        data = defaults or {}
        data.update(**self.model_dump(exclude_unset=True, exclude=exclude))
        data.update(**kwarg)
        obj = obj.update_from_dict(data)
        await obj.save()
        await self.update_m2m(obj, m2m)
        if serialize:
            return await call(
                (serializer or self.__class__).from_tortoise_orm,
                (serializer or self.__class__),
                obj,
                m2m=[(m[0], m[0]) for m in m2m],
            )
        return obj


class BaseResponseScheme(BaseCreateScheme):
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
