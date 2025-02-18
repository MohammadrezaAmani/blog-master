from fastapi import APIRouter

from src.helper import add_patterns
from src.helper.minio.api.file import router as file_router

api_patterns = [
    (file_router, "/file", ["File"], {}),
]

router = add_patterns(APIRouter(), api_patterns)
