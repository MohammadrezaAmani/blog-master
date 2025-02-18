from fastapi import APIRouter

from src.helper import add_patterns
from src.helper.permission.api.group import router as group_router

api_patterns = [
    (group_router, "/group", ["Group"], {}),
]

router = add_patterns(APIRouter(), api_patterns)
