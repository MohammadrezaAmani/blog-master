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
from src.helper.common import Action, ActionCreateScheme, ActionResponseScheme
from src.helper.user.model import User

router = APIRouter()

ActionFilterSchema = create_filter_schema(Action)

MODEL_NAME: str = Action._meta.db_table


@router.get(
    "/", response_model=Paginated[ActionResponseScheme] | List[ActionResponseScheme]
)
@log_action(action=ActionEnum.VIEW_ALL.value, model=MODEL_NAME)
@has_access(action=ActionEnum.VIEW_ALL.value, to=MODEL_NAME)
async def get_actions_router(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),
    filters: ActionFilterSchema = Depends(),  # type: ignore
    user: User = Depends(login_required),
    sort_by: list[str] = Query([]),
    pagination: bool = Query(True),
):
    objects = Action.all()
    sort = OrderBy.create(objects, sort_by)
    objects = Filter.create(sort, filters)
    return await Paginator(limit=limit, page=page).paginated(
        ActionResponseScheme, objects, apply=pagination
    )


@router.post("/", response_model=ActionResponseScheme)
@log_action(action=ActionEnum.CREATE.value, model=MODEL_NAME)
@has_access(action=ActionEnum.CREATE.value, to=MODEL_NAME)
async def create_action_router(
    object: ActionCreateScheme,
    user: User = Depends(login_required),
):
    return await object.create(
        Action,
        serialize=True,
        serializer=ActionResponseScheme,
        m2m=[],
        user_id=user.id,
    )


@router.get("/{id}", response_model=ActionResponseScheme)
@log_action(action=ActionEnum.VIEW.value, model=MODEL_NAME)
@has_access(action=ActionEnum.VIEW.value, to=MODEL_NAME)
async def get_action_router(
    id: str,
    request: Request,
    user: User = Depends(login_required),
):
    objects = Action.all()
    return await ActionResponseScheme.from_tortoise_orm(
        ActionResponseScheme,
        await objects.get(Q(id=id) if str(id).isdigit() else Q(slug=str(id))),
    )


@router.put("/{id}", response_model=ActionResponseScheme)
@log_action(action=ActionEnum.UPDATE.value, model=MODEL_NAME)
@has_access(action=ActionEnum.UPDATE.value, to=MODEL_NAME)
async def update_action_router(
    id: int,
    object: ActionCreateScheme,
    user: User = Depends(login_required),
):
    objects = Action.all()
    return await object.update(
        await objects.get(id=id),
        serialize=True,
        serializer=ActionResponseScheme,
        m2m=[],
        user_id=user.id,
    )


@router.delete("/{id}", response_model=Status)
@log_action(action=ActionEnum.DELETE.value, model=MODEL_NAME)
@has_access(action=ActionEnum.DELETE.value, to=MODEL_NAME)
async def delete_action_router(id: int, user: User = Depends(login_required)):
    objects = Action.filter().all()
    deleted_count = await objects.filter(id=id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail=f"Action {id} not found")
    return Status(message=f"Deleted action {id}")
