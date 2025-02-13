from src.base.scheme import BaseCreateScheme, BaseResponseScheme


class PermissionCreateScheme(BaseCreateScheme):
    name: str
    to: str
    action: str
    description: str | None = None


class PermissionResponseScheme(PermissionCreateScheme, BaseResponseScheme): ...


class GroupCreateScheme(BaseCreateScheme):
    name: str
    parent_id: int | None = None


class GroupResponseScheme(GroupCreateScheme, BaseResponseScheme): ...
