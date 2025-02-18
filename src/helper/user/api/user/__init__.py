from fastapi import APIRouter

from src.config.settings import USE_MINIO
from src.helper import add_patterns
from src.helper.user.api.user.user import router as user_router

url_patterns = []
if USE_MINIO:
    from src.helper.user.api.user.profile import router as profile_apis

    url_patterns += [
        (profile_apis, "/user/{user_id}/profile", ["Profile"]),
    ]
url_patterns += [
    (user_router, "", ["User"]),
]

router = add_patterns(APIRouter(), url_patterns)
