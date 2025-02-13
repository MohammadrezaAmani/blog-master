from inspect import iscoroutinefunction


async def call(function, *args, **kwargs):
    if iscoroutinefunction(function):
        return await function(*args, **kwargs)
    return function(*args, **kwargs)
