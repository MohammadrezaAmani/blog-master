from fastapi import APIRouter

from src.helper import add_patterns
from src.helper.common.api.action import router as action_router
from src.helper.common.api.category import router as category_router
from src.helper.common.api.comment import router as comment_router
from src.helper.common.api.language import router as language_router
from src.helper.common.api.react import router as react_router
from src.helper.common.api.tag import router as tag_router

api_patterns = [
    (language_router, "/language", ["Language"], {}),
    (tag_router, "/tag", ["Tag"], {}),
    (action_router, "/action", ["Action"], {}),
    (react_router, "/react", ["React"], {}),
    (comment_router, "/comment", ["Comment"], {}),
    (category_router, "/category", ["Category"], {}),
]

router = add_patterns(APIRouter(), api_patterns)
