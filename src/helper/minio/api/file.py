import mimetypes
from typing import List

from fastapi import APIRouter, Depends
from fastapi import File as FastAPIFile
from fastapi import HTTPException, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from src.config.settings import MINIO_BASE_BUCKETS
from src.helper import (
    ActionEnum,
    Filter,
    OrderBy,
    create_filter_schema,
    log_action,
    login_required,
)
from src.helper.minio import File, FileCreateScheme, FileResponseScheme
from src.helper.paginate import Paginated, Paginator
from src.helper.user import Status
from src.helper.user.model import User
from tortoise.queryset import Q


def get_file_type(file_name: str) -> str:
    file_type, _ = mimetypes.guess_type(file_name)
    return file_type or "application/octet-stream"  #


router = APIRouter()


FileFilterSchema = create_filter_schema(File)


@router.get(
    "/", response_model=Paginated[FileResponseScheme] | List[FileResponseScheme]
)
@log_action(action=ActionEnum.VIEW.value, model="File")
async def get_files_router(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),
    filters: FileFilterSchema = Depends(),  # type: ignore
    user=Depends(login_required),
    sort_by: list[str] = Query([]),
    pagination: bool = Query(True),
):
    sort = OrderBy.create(File.all(), sort_by)
    objects = Filter.create(sort, filters)
    return await Paginator(limit=limit, page=page).paginated(
        FileResponseScheme, objects, pagination
    )


@router.post("/")  # , response_model=FileResponseScheme)
async def create_file_router(
    user: User = Depends(login_required),
    file: UploadFile = FastAPIFile(...),
):
    obj, file_url = await File.upload(file, user)

    return {
        "message": "File uploaded successfully",
        "file_name": obj.url,
        "file_url": file_url,
    }


@router.get("/{id}", response_model=FileResponseScheme)
@log_action(action=ActionEnum.VIEW.value, model="File")
async def get_file_router(
    id: str,
    request: Request,
    user=Depends(login_required),
    as_file: bool = Query(False),
):
    obj = await File.get(Q(id=id) if str(id).isdigit() else Q(slug=str(id)))
    response = await FileResponseScheme.from_tortoise_orm(
        FileResponseScheme,
        obj,
    )
    if as_file:
        file = response.file
        return StreamingResponse(
            file,
            media_type=get_file_type(response.name),
            headers={
                "Content-Disposition": f"attachment; filename={response.name}",
                "X-File-Name": response.name,
            },
        )
    return response


@router.put("/{id}", response_model=FileResponseScheme)
async def update_file_router(
    id: int,
    object: FileCreateScheme,
    user=Depends(login_required),
):
    file = await object.create(
        user.id, MINIO_BASE_BUCKETS[0], url=(await File.get(id=id)).url
    )
    return await FileResponseScheme.from_tortoise_orm(FileResponseScheme, file)


@router.delete("/{id}", response_model=Status)
async def delete_file_router(id: int):
    #! add remove from minio
    deleted_count = await File.filter(id=id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail=f"File {id} not found")
    return Status(message=f"Deleted file {id}")
