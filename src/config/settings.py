import os

from decouple import config

DEBUG = True
DB_URL = "sqlite://db.sqlite3"

APPS = [
    "src.helper.permission.model",
    "src.helper.logger.model",
    "src.helper.user.model",
    "src.helper.common.model",
    "src.app.project.model",
]


USE_MINIO = config("USE_MINIO", cast=bool, default=False)
USE_REDIS = config("USE_REDIS", cast=bool, default=False)


if USE_MINIO:
    APPS.append("src.helper.minio.model")

USER_MODEL = "models.User"
USER_MODEL_PATH = "src.helper.user.model"

GENERATE_SCHEMES = True
ADD_EXCEPTION_HANDLERS = True

USE_TZ = False
TIMEZONE = "Asia/Tehran"

SENDGRID_API_KEY = ""
FROM_EMAIL = ""

SECRET_KEY = "JWT_KEY"
REFRESH_SECRET_KEY = "JWT_REFRESH_KEY"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
JWT_HASH_ALGORITHM = "HS256"

TORTOISE_ORM = {
    "connections": {"default": os.getenv("DB_URL", DB_URL)},
    "apps": {
        "models": {
            "models": [*APPS, "aerich.models"],
            "default_connection": "default",
        },
    },
    "use_tz": USE_TZ,
    "timezone": TIMEZONE,
}

CACHE_TTL = config("CACHE_TTL", cast=int, default=3600)

if USE_MINIO:
    MINIO_HOST = config("MINIO_HOST", default="192.168.10.53")
    MINIO_PORT = config("MINIO_PORT", cast=int, default=9000)
    AWS_ACCESS_KEY = "p3HcYZqccEk50mgVd08V"  # config("AWS_ACCESS_KEY", default="")
    AWS_SECRET_ACCESS_KEY = "ZkCcW5YWUCXXyPMa6ZMXrXWCD6uJK57tFKO1ynP4"  # config("AWS_SECRET_ACCESS_KEY", default="")
    MINIO_BASE_BUCKETS = config("MINIO_BASE_BUCKETS", default="files,images").split(",")
    MINIO_URI = f"{MINIO_HOST}:{MINIO_PORT}"
    MINIO_KWARGS = {}

if USE_REDIS:
    REDIS_HOST = config("REDIS_HOST", default="127.0.0.1")
    REDIS_PORT = config("REDIS_PORT", cast=int, default=6379)
    REDIS_USERNAME = config("REDIS_USERNAME", default=None)
    REDIS_PASSWORD = config("REDIS_PASSWORD", default=None)
    REDIS_URI = f"redis://{REDIS_HOST}:{REDIS_PORT}"
    REDIS_KWARGS = {}


SHOW_QUERIES_IN_SWAGGER = False

FILTER_OPERATIONS = [
    "exact",
    # "iexact",
    "contains",
    "icontains",
    # "gt",
    # "gte",
    # "lt",
    # "lte",
    "in",
    "isnull",
    "startswith",
    # "istartswith",
    # "endswith",
    # "iendswith",
    # "range",
    # "year",
    # "month",
    # "day",
    # "week",
    # "hour",
    # "minute",
    # "second",
    # "date",
    # "time",
    # "datetime",
    # "is",
    # "isnull",
    # "regex",
    # "iregex",
    # "count",
    # "sum",
    # "avg",
    # "exists",
]


SMTP_SERVER = ""
SMTP_PORT = 587
SMTP_USERNAME = ""
SMTP_PASSWORD = ""
DEFAULT_FROM_EMAIL = ""
