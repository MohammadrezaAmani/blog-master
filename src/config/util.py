import importlib
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Type

from fastapi import FastAPI
from src.config.settings import TORTOISE_ORM, USE_MINIO, USER_MODEL, USER_MODEL_PATH
from tortoise import Model, Tortoise, generate_config
from tortoise.contrib.fastapi import RegisterTortoise


def remove_queries_from_swagger(app: FastAPI):
    app.openapi_schema = app.openapi()
    for path in app.openapi_schema["paths"].values():
        for operation in path.values():
            if isinstance(operation, dict) and "parameters" in operation:
                operation["parameters"] = [
                    param for param in operation["parameters"] if param["in"] != "query"
                ]


@asynccontextmanager
async def lifespan_test(app: FastAPI) -> AsyncGenerator[None, None]:
    config = generate_config(
        os.getenv("TORTOISE_TEST_DB", "sqlite://:memory:"),
        app_modules={"models": ["models"]},
        testing=True,
        connection_label="models",
    )
    async with RegisterTortoise(
        app=app,
        config=config,
        generate_schemas=True,
        add_exception_handlers=True,
        _create_db=True,
    ):
        yield
    await Tortoise._drop_databases()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    if USE_MINIO:
        from src.config.settings import MINIO_BASE_BUCKETS
        from src.helper.minio.controller import ensure_bucket_exists

        await ensure_bucket_exists(MINIO_BASE_BUCKETS)

    if getattr(app.state, "testing", None):
        async with lifespan_test(app) as _:
            yield
    else:
        await Tortoise.init(config=TORTOISE_ORM)
        await Tortoise.generate_schemas()
        try:
            yield
        finally:
            await Tortoise.close_connections()


def get_user_model() -> Type[Model]:
    user_model = importlib.import_module(USER_MODEL_PATH)
    return getattr(user_model, USER_MODEL.split(".")[-1])
