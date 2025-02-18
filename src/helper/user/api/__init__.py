from fastapi import APIRouter

from src.helper import add_patterns
from src.helper.user.api.auth import router as auth_router
from src.helper.user.api.user import router as user_router

url_patterns = [
    (auth_router, "/auth", ["Auth"]),
    (user_router, ""),
]

router = add_patterns(APIRouter(), url_patterns)
