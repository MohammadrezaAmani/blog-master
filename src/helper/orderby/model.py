from fastapi import HTTPException
from tortoise.queryset import QuerySet


class OrderBy:
    def __init__(self):
        self.data: list[str] = []

    def add(self, field: str):
        self.data.append(field)

    def apply(self, query: QuerySet):
        return query.order_by(*(self.data))

    @staticmethod
    def create(
        query: QuerySet,
        sort_by: list[str],
        exclude: list[str] = None,
        allowed_fields: list[str] = None,
    ):
        order_obj = OrderBy()
        exclude = exclude or []
        for field in sort_by:
            try:
                if (
                    field.replace("-", "").split("__")[0] in exclude
                    or field.replace("-", "") in exclude
                ):
                    continue
                if allowed_fields and field.replace("-", "") in allowed_fields:
                    continue
                order_obj.add(field)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid order format: {field}"
                )
        return order_obj.apply(query)
