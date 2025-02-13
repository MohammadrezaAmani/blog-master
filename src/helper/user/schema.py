from src.base.scheme import BaseCreateScheme, BaseResponseScheme


class UserResponseScheme(BaseResponseScheme):
    name: str
    username: str
    is_active: bool = True
    mobile: str | None = None
    group_id: int | None = None


class UserCreateScheme(BaseCreateScheme):
    name: str
    username: str
    password: str | None = None
    is_active: bool = True
    mobile: str | None = None
    group_id: int | None = None
