from typing import List

from fastapi import APIRouter, Depends
from fastapi import File as FastAPIFile
from fastapi import HTTPException, Query, Request, UploadFile

from src.helper.auth import login_required
from src.helper.filters import Filter, create_filter_schema
from src.helper.logger import ActionEnum, log_action
from src.helper.minio.model import File
from src.helper.minio.schema import FileResponseScheme
from src.helper.orderby import OrderBy
from src.helper.paginate import Paginated, Paginator
from src.helper.scheme import Status
from src.helper.user import User

router = APIRouter()


UserFilterSchema = create_filter_schema(User, ["password"])


@router.get(
    "/", response_model=Paginated[FileResponseScheme] | List[FileResponseScheme]
)
@log_action(action=ActionEnum.VIEW.value, model="User")
async def get_profiles_router(
    user_id: int,
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=10000),
    filters: UserFilterSchema = Depends(),  # type: ignore
    user: User = Depends(login_required),
    sort_by: list[str] = Query([]),
    pagination: bool = Query(True),
):
    sort = OrderBy.create((await User.get(id=user_id)).image.all(), sort_by)
    objects = Filter.create(sort, filters)
    return await Paginator(limit=limit, page=page).paginated(
        FileResponseScheme, objects, pagination
    )


@router.post("/", response_model=FileResponseScheme)
async def create_file_router(
    user_id: int,
    user: User = Depends(login_required),
    file: UploadFile = FastAPIFile(...),
):
    obj, file_url = await File.upload(file, user)
    await (await User.get(id=user_id)).image.add(obj)
    return await FileResponseScheme.from_tortoise_orm(FileResponseScheme, obj)


@router.get("/{id}", response_model=FileResponseScheme)
async def get_profile_router(user_id: int, id: int):
    return await FileResponseScheme.from_tortoise_orm(
        FileResponseScheme, await File.get(id=id)
    )


@router.delete("/{id}", response_model=Status)
async def delete_profile_router(user_id: int, id: int):
    deleted_count = await File.filter(id=id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail=f"User {id} not found")
    return Status(message=f"Deleted user {id}")
