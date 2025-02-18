from fastapi import APIRouter

from src.app.blog.api.post import router as post_router
from src.helper import add_patterns

api_patterns = [
    (post_router, "/post", ["Post"], {}),
]

router = add_patterns(APIRouter(), api_patterns)
