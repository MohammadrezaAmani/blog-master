from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.config import (
    DEBUG,
    SHOW_QUERIES_IN_SWAGGER,
    api_router,
    lifespan,
    remove_queries_from_swagger,
)

app = FastAPI(title="Blog Master Backend", lifespan=lifespan, debug=DEBUG)
if DEBUG:
    from debug_toolbar.middleware import DebugToolbarMiddleware

    app.add_middleware(
        DebugToolbarMiddleware,
        panels=["debug_toolbar.panels.tortoise.TortoisePanel"],
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["127.0.0.1", "localhost"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
app.include_router(api_router, prefix="")


if not SHOW_QUERIES_IN_SWAGGER:
    remove_queries_from_swagger(app)
