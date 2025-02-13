from src.config.settings import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    APPS,
    DEBUG,
    FILTER_OPERATIONS,
    JWT_HASH_ALGORITHM,
    REFRESH_SECRET_KEY,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SECRET_KEY,
    SHOW_QUERIES_IN_SWAGGER,
    TORTOISE_ORM,
    USER_MODEL,
    USER_MODEL_PATH,
)
from src.config.url import api_router
from src.config.util import lifespan, remove_queries_from_swagger

__all__ = [
    "DEBUG",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "APPS",
    "FILTER_OPERATIONS",
    "JWT_HASH_ALGORITHM",
    "REFRESH_SECRET_KEY",
    "REFRESH_TOKEN_EXPIRE_DAYS",
    "SECRET_KEY",
    "SHOW_QUERIES_IN_SWAGGER",
    "TORTOISE_ORM",
    "USER_MODEL",
    "USER_MODEL_PATH",
    "api_router",
    "remove_queries_from_swagger",
    "lifespan",
]
