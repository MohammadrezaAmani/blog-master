from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from src.helper.auth import login_required
from src.helper.filters import Filter, create_filter_schema
from src.helper.logger import ActionEnum, log_action
from src.helper.orderby import OrderBy
from src.helper.paginate import Paginated, Paginator
from src.helper.scheme import Status
from src.helper.user import User, UserCreateScheme, UserResponseScheme

router = APIRouter()


UserFilterSchema = create_filter_schema(User, ["password"])


@router.get(
    "/", response_model=Paginated[UserResponseScheme] | List[UserResponseScheme]
)
@log_action(action=ActionEnum.VIEW.value, model="User")
# @has_access(action=Access.READ, to=ToUserApp.user)
async def get_user(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=10000),
    filters: UserFilterSchema = Depends(),  # type: ignore
    user: User = Depends(login_required),
    sort_by: list[str] = Query([]),
    pagination: bool = Query(True),
):
    sort = OrderBy.create(User.all(), sort_by)
    objects = Filter.create(sort, filters)
    return await Paginator(limit=limit, page=page).paginated(
        UserResponseScheme, objects, pagination
    )


@router.post("/", response_model=UserResponseScheme)
# @has_access(action=Access.CREATE, to=ToUserApp.user)
async def create_user(obj: UserCreateScheme, user: User = Depends(login_required)):
    return await obj.create(
        User,
        serialize=True,
        serializer=UserResponseScheme,
    )
    # user_obj = await User.create(**obj.model_dump(exclude_unset=True))
    # return await UserResponseScheme.from_tortoise_orm(UserResponseScheme, user_obj)


@router.get("/{id}", response_model=UserResponseScheme)
# @has_access(action=Access.READ, to=ToUserApp.user)
async def get_users(id: int):
    return await UserResponseScheme.from_tortoise_orm(
        UserResponseScheme, await User.get(id=id)
    )


@router.put("/{user_id}", response_model=UserResponseScheme)
async def update_user(user_id: int, user: UserCreateScheme):
    obj = await User.get(id=user_id)
    password_changed = bool(user.password)
    result = obj.update_from_dict(
        user.model_dump(
            exclude_unset=True, exclude={"id", "created_at", "updated_at", "password"}
        )
    )
    if password_changed:
        result.password = user.password

    await result.save(password_changed=password_changed)
    return await UserResponseScheme.from_tortoise_orm(UserResponseScheme, result)


@router.delete("/{user_id}", response_model=Status)
# @has_access(action=Access.DELETE, to=ToUserApp.user)
async def delete_user(user_id: int):
    deleted_count = await User.filter(id=user_id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return Status(message=f"Deleted user {user_id}")
