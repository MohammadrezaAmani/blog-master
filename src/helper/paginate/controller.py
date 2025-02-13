from functools import wraps
from typing import Callable

from .models import BasePaginator, Paginator


def paginate(limit: int = 10, page: int = 1, paginator: BasePaginator = Paginator):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            page_value = kwargs.get("page", page)
            limit_value = kwargs.get("limit", limit)

            result = await func(*args, **kwargs)

            return await paginator(result, limit_value, page_value).paginate()

        return wrapper

    return decorator
