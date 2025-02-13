from typing import Any

from fastapi import HTTPException
from tortoise import Model
from tortoise.queryset import QuerySet, QuerySetSingle


def remove_excludes(
    query: QuerySet | list[dict[str, Any]],
    model: Model,
    exclude: list,
    allowed_fields: list[str] = None,
):
    if isinstance(query, QuerySet):
        return query.values(
            *[
                field
                for field in (allowed_fields or model._meta.fields_map.keys())
                if field not in exclude
                and not hasattr(
                    model._meta.fields_map[field],
                    "related_model",
                )
                and not hasattr(model._meta.fields_map[field], "related_objects")
            ]
        )
    if isinstance(query, model):
        print(getattr(query, "id"), model._meta.fields_map.keys())
        return {
            key: getattr(query, key)
            for key in (allowed_fields or model._meta.fields_map.keys())
            if key not in exclude
            and not hasattr(
                model._meta.fields_map[key],
                "related_model",
            )
            and not hasattr(model._meta.fields_map[key], "related_objects")
        }
    return [
        [
            getattr(item, key) if hasattr(item, key) else item[key]
            for key in (allowed_fields or model._meta.fields_map.keys())
            if key not in exclude
        ]
        for item in query
    ]


class Select:
    def __init__(self):
        self.data: list[str] = []

    def add(self, field: str):
        self.data.append(field)

    def apply(
        self, query: QuerySet | list[dict[str, Any]] | QuerySetSingle, model: Model
    ):
        if isinstance(query, model):
            return {
                key: getattr(query, key)
                for key in self.data
                if not hasattr(
                    model._meta.fields_map[key],
                    "related_model",
                )
                and not hasattr(model._meta.fields_map[key], "related_objects")
            }
        if isinstance(query, (set, list, tuple)):
            return [
                {key: getattr(item, key) for key in self.data if key} for item in query
            ]

        return query.values(*list(set(self.data)))

    @staticmethod
    def create(
        query: QuerySet | list[dict[str, Any]],
        select: list[str],
        model: Model,
        exclude: list[str] = None,
        allowed_fields: list[str] = None,
    ):
        exclude = exclude or []
        if not select:
            return remove_excludes(query, model, exclude, allowed_fields)
        select_obj = Select()
        for field in select:
            try:
                if (
                    field.replace("-", "").split("__")[0] in exclude
                    or field.replace("-", "") in exclude
                ):
                    continue
                if allowed_fields and field.replace("-", "") in allowed_fields:
                    continue
                select_obj.add(field)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid order format: {field}"
                )
        return select_obj.apply(query, model)
