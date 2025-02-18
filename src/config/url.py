from fastapi import APIRouter

from src.app.blog.api import router as blog_router
from src.config.settings import USE_MINIO
from src.helper import add_patterns
from src.helper.common.api import router as common_router
from src.helper.permission.api import router as permission_router
from src.helper.user.api import router as user_router

if USE_MINIO:
    from src.helper.minio.api import router as minio_router

api_patterns = [
    (user_router, "/user"),
    (common_router, "/c"),
    (permission_router,),
    (blog_router,),
]

if USE_MINIO:
    api_patterns += [(minio_router,)]
api_router = add_patterns(APIRouter(prefix="/api"), api_patterns)
