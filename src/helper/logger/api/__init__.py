from fastapi import APIRouter

from src.helper.url import add_patterns

from .log import router as log_router

url_patterns = [
    (log_router, "/log", ["Log"]),
]

router = add_patterns(APIRouter(), url_patterns)
