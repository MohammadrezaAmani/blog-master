from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from tortoise.queryset import Q

from src.helper import (
    ActionEnum,
    Filter,
    OrderBy,
    Paginator,
    Status,
    create_filter_schema,
    log_action,
    login_required,
)
from src.helper.paginate import Paginated
from src.helper.permission import Group, GroupCreateScheme, GroupResponseScheme

router = APIRouter()


GroupFilterSchema = create_filter_schema(Group)


@router.get(
    "/", response_model=Paginated[GroupResponseScheme] | List[GroupResponseScheme]
)
@log_action(action=ActionEnum.VIEW.value, model="Group")
async def get_groups_router(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),
    filters: GroupFilterSchema = Depends(),  # type: ignore
    user=Depends(login_required),
    sort_by: list[str] = Query([]),
    pagination: bool = Query(True),
):
    sort = OrderBy.create(Group.all(), sort_by)
    objects = Filter.create(sort, filters)
    return await Paginator(limit=limit, page=page).paginated(
        GroupResponseScheme, objects, pagination
    )


@router.post("/", response_model=GroupResponseScheme)
async def create_group_router(
    object: GroupCreateScheme,
    user=Depends(login_required),
):
    return await object.create(Group, serialize=True, serializer=GroupResponseScheme)


@router.get("/{id}", response_model=GroupResponseScheme)
@log_action(action=ActionEnum.VIEW.value, model="Group")
async def get_group_router(
    id: str,
    request: Request,
    user=Depends(login_required),
):
    return await GroupResponseScheme.from_tortoise_orm(
        GroupResponseScheme,
        await Group.get(Q(id=id) if str(id).isdigit() else Q(slug=str(id))),
    )


@router.put("/{id}", response_model=GroupResponseScheme)
async def update_group_router(
    id: int,
    object: GroupCreateScheme,
    user=Depends(login_required),
):
    await Group.filter(id=id).update(**object.model_dump(exclude_unset=True))
    return await GroupResponseScheme.from_tortoise_orm(await Group.get(id=id))


@router.delete("/{id}", response_model=Status)
async def delete_group_router(id: int):
    deleted_count = await Group.filter(id=id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail=f"Group {id} not found")
    return Status(message=f"Deleted group {id}")
