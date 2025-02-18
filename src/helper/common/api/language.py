from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from tortoise.queryset import Q

from src.helper import (
    ActionEnum,
    Filter,
    OrderBy,
    Paginated,
    Paginator,
    Status,
    create_filter_schema,
    has_access,
    log_action,
    login_required,
)
from src.helper.common import Language, LanguageCreateScheme, LanguageResponseScheme
from src.helper.user.model import User

router = APIRouter()

LanguageFilterSchema = create_filter_schema(Language)

MODEL_NAME: str = Language._meta.db_table


@router.get(
    "/", response_model=Paginated[LanguageResponseScheme] | List[LanguageResponseScheme]
)
@log_action(action=ActionEnum.VIEW_ALL.value, model=MODEL_NAME)
@has_access(action=ActionEnum.VIEW_ALL.value, to=MODEL_NAME)
async def get_languages_router(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),
    filters: LanguageFilterSchema = Depends(),  # type: ignore
    user: User = Depends(login_required),
    sort_by: list[str] = Query([]),
    pagination: bool = Query(True),
):
    objects = Language.all()
    sort = OrderBy.create(objects, sort_by)
    objects = Filter.create(sort, filters)
    return await Paginator(limit=limit, page=page).paginated(
        LanguageResponseScheme, objects, apply=pagination
    )


@router.post("/", response_model=LanguageResponseScheme)
@log_action(action=ActionEnum.CREATE.value, model=MODEL_NAME)
@has_access(action=ActionEnum.CREATE.value, to=MODEL_NAME)
async def create_language_router(
    object: LanguageCreateScheme,
    user: User = Depends(login_required),
):
    return await object.create(
        Language,
        serialize=True,
        serializer=LanguageResponseScheme,
        m2m=[],
    )


@router.get("/{id}", response_model=LanguageResponseScheme)
@log_action(action=ActionEnum.VIEW.value, model=MODEL_NAME)
@has_access(action=ActionEnum.VIEW.value, to=MODEL_NAME)
async def get_language_router(
    id: str,
    request: Request,
    user: User = Depends(login_required),
):
    objects = Language.all()
    return await LanguageResponseScheme.from_tortoise_orm(
        LanguageResponseScheme,
        await objects.get(Q(id=id) if str(id).isdigit() else Q(slug=str(id))),
    )


@router.put("/{id}", response_model=LanguageResponseScheme)
@log_action(action=ActionEnum.UPDATE.value, model=MODEL_NAME)
@has_access(action=ActionEnum.UPDATE.value, to=MODEL_NAME)
async def update_language_router(
    id: int,
    object: LanguageCreateScheme,
    user: User = Depends(login_required),
):
    objects = Language.all()
    return await object.update(
        await objects.get(id=id),
        serialize=True,
        serializer=LanguageResponseScheme,
        m2m=[],
    )


@router.delete("/{id}", response_model=Status)
@log_action(action=ActionEnum.DELETE.value, model=MODEL_NAME)
@has_access(action=ActionEnum.DELETE.value, to=MODEL_NAME)
async def delete_language_router(id: int, user: User = Depends(login_required)):
    objects = Language.filter().all()
    deleted_count = await objects.filter(id=id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail=f"Language {id} not found")
    return Status(message=f"Deleted language {id}")
