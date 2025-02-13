from functools import wraps

from fastapi import HTTPException, Request
from src.helper.permission.model import Permission


async def has_permission(user, permission):
    return await user.group.filter(permissions=permission).exists()


class Access:
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    PATCH = "patch"


class ToUserApp:
    user = "models.User"


def has_access(
    name: str | None = None,
    action: str | None = None,
    to: str | None = None,
    request_field: str = "request",
    user_field: str = "user",
):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get(user_field)
            request: Request = kwargs.get(request_field)
            act = action
            if not act:
                act = request.method.lower()
            if not user:
                raise HTTPException(
                    status_code=401, detail="User authentication required"
                )
            if act and to:
                permission = await Permission.get_or_none(action=act, to=to)
                if not permission:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Permission for action '{act}' on '{to}' not found",
                    )
                if not await has_permission(user, permission):
                    raise HTTPException(
                        status_code=403,
                        detail=f"User does not have permission for action '{act}' on '{to}'",
                    )
            elif name:
                permission = await Permission.get_or_none(name=name)
                if not permission:
                    raise HTTPException(
                        status_code=403, detail=f"Permission '{name}' not found"
                    )
                if not await has_permission(user, permission):
                    raise HTTPException(
                        status_code=403,
                        detail=f"User does not have permission '{name}'",
                    )

            result = await func(*args, **kwargs)
            return result

        return wrapper

    return decorator
