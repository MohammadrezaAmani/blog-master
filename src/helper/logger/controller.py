from functools import wraps

from fastapi import Request
from tortoise import Model

from .model import Log  # noqa


async def add_log(
    request: Request, user_id, action, model, model_id, success: bool = True
):
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent", "")
    mac_address = None
    browser = user_agent.split(" ")[0] if user_agent else "unknown"
    location = None
    await Log.create(
        user_id=user_id,
        action=action,
        db_model=model,
        db_model_id=model_id,
        ip_address=ip_address,
        mac_address=mac_address,
        browser=browser,
        user_agent=user_agent,
        location=location,
        is_success=success,
    )


def log_action(
    action: str,
    model: str | Model,
    model_id_field: str = "id",
    request_field: str = "request",
    user_field: str = "user",
):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get(request_field)
            user = kwargs.get(user_field)
            model_id = kwargs.get(model_id_field)
            success = False
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            finally:
                if user:
                    user_id = user.id
                    if request and user_id:
                        await add_log(
                            request=request,
                            user_id=user_id,
                            action=action,
                            model=model,
                            model_id=model_id,
                            success=success,
                        )

        return wrapper

    return decorator
