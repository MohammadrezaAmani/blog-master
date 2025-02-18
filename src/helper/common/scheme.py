from src.base.scheme import BaseCreateScheme, BaseResponseScheme


class LanguageCreateScheme(BaseCreateScheme):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    data: dict | None = None


class LanguageResponseScheme(LanguageCreateScheme, BaseResponseScheme): ...


class TagCreateScheme(BaseCreateScheme):
    name: str | None = None


class TagResponseScheme(TagCreateScheme, BaseResponseScheme): ...


class ActionCreateScheme(BaseCreateScheme):
    name: str | None = None
    user_id: int
    to_id: int
    description: str | None = None


class ActionResponseScheme(ActionCreateScheme, BaseResponseScheme): ...


class ReactCreateScheme(BaseCreateScheme):
    name: str | None = None
    user_id: int
    description: str | None = None


class ReactResponseScheme(ReactCreateScheme, BaseResponseScheme): ...


class CommentCreateScheme(BaseCreateScheme):
    text: str
    user_id: int
    react: list[int] | None = None
    tag: list[int] | None = None
    vote: int | None = None


class CommentResponseScheme(CommentCreateScheme, BaseResponseScheme): ...


class CategoryCreateScheme(BaseCreateScheme):
    name: str
    user_id: int | None = None
    react: list[int] | None = None
    tag: list[int] | None = None
    parent: list[int] | None = None
    comment: list[int] | None = None
    description: str | None = None


class CategoryResponseScheme(CategoryCreateScheme, BaseResponseScheme): ...
