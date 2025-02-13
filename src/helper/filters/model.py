from typing import Any, Dict

from fastapi import HTTPException
from pydantic import BaseModel
from tortoise.queryset import QuerySet


class Filter:
    def __init__(self):
        self.data: Dict[str, Any] = {}

    def add(self, field_name: str, operator: str | None, value: Any):
        if value is not None:
            if operator:
                full_field_name = f"{field_name}__{operator}"
            else:
                full_field_name = field_name
            self.data[full_field_name] = value

    def apply(self, query: QuerySet):
        q = query.filter(**self.data)
        return q

    @staticmethod
    def create(query: QuerySet, filters: BaseModel, exclude: list[str] = None):
        filter_obj = Filter()
        exclude = exclude or []
        for field_with_op, value in filters.model_dump(exclude_none=True).items():
            try:
                if "__" in field_with_op:
                    field, operator = field_with_op.split("__")
                else:
                    field, operator = field_with_op, None
                if field in exclude:
                    continue
                filter_obj.add(field, operator, value)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid filter format: {field_with_op}"
                )
        return filter_obj.apply(query)
