from fastapi import APIRouter
from src.helper import add_patterns
from src.helper.user.api.user.profile import router as profile_apis
from src.helper.user.api.user.user import router as user_router

url_patterns = [
    (profile_apis, "/user/{user_id}/profile", ["Profile"]),
    (user_router, "", ["User"]),
]

router = add_patterns(APIRouter(), url_patterns)
