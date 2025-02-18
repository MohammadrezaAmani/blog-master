from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from tortoise.queryset import Q

from src.app.blog import Post, PostCreateScheme, PostResponseScheme
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
from src.helper.user.model import User

router = APIRouter()

PostFilterSchema = create_filter_schema(Post)

MODEL_NAME: str = Post._meta.db_table


@router.get(
    "/", response_model=Paginated[PostResponseScheme] | List[PostResponseScheme]
)
@log_action(action=ActionEnum.VIEW_ALL.value, model=MODEL_NAME)
@has_access(action=ActionEnum.VIEW_ALL.value, to=MODEL_NAME)
async def get_posts_router(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),
    filters: PostFilterSchema = Depends(),  # type: ignore
    user: User = Depends(login_required),
    sort_by: list[str] = Query([]),
    pagination: bool = Query(True),
):
    objects = Post.all()
    sort = OrderBy.create(objects, sort_by)
    objects = Filter.create(sort, filters)
    return await Paginator(limit=limit, page=page).paginated(
        PostResponseScheme, objects, apply=pagination
    )


@router.post("/", response_model=PostResponseScheme)
@log_action(action=ActionEnum.CREATE.value, model=MODEL_NAME)
@has_access(action=ActionEnum.CREATE.value, to=MODEL_NAME)
async def create_post_router(
    object: PostCreateScheme,
    user: User = Depends(login_required),
):
    return await object.create(
        Post,
        serialize=True,
        serializer=PostResponseScheme,
        m2m=[],
    )


@router.get("/{id}", response_model=PostResponseScheme)
@log_action(action=ActionEnum.VIEW.value, model=MODEL_NAME)
@has_access(action=ActionEnum.VIEW.value, to=MODEL_NAME)
async def get_post_router(
    id: str,
    request: Request,
    user: User = Depends(login_required),
):
    objects = Post.all()
    return await PostResponseScheme.from_tortoise_orm(
        PostResponseScheme,
        await objects.get(Q(id=id) if str(id).isdigit() else Q(slug=str(id))),
    )


@router.put("/{id}", response_model=PostResponseScheme)
@log_action(action=ActionEnum.UPDATE.value, model=MODEL_NAME)
@has_access(action=ActionEnum.UPDATE.value, to=MODEL_NAME)
async def update_post_router(
    id: int,
    object: PostCreateScheme,
    user: User = Depends(login_required),
):
    objects = Post.all()
    return await object.update(
        await objects.get(id=id),
        serialize=True,
        serializer=PostResponseScheme,
        m2m=[],
    )


@router.delete("/{id}", response_model=Status)
@log_action(action=ActionEnum.DELETE.value, model=MODEL_NAME)
@has_access(action=ActionEnum.DELETE.value, to=MODEL_NAME)
async def delete_post_router(id: int, user: User = Depends(login_required)):
    objects = Post.filter().all()
    deleted_count = await objects.filter(id=id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail=f"Post {id} not found")
    return Status(message=f"Deleted post {id}")
