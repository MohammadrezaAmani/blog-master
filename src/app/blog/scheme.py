from src.base.scheme import BaseCreateScheme, BaseResponseScheme


class PostCreateScheme(BaseCreateScheme):
    title: str | None = None
    body: str | None = None
    user_id: int | None = None
    react: list[int] | None = None
    comment: list[int] | None = None
    category: list[int] | None = None
    tag: list[int] | None = None
    related_post: list[int] | None = None


class PostResponseScheme(PostCreateScheme, BaseResponseScheme): ...
