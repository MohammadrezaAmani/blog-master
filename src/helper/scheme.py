from pydantic import BaseModel


class Status(BaseModel):
    message: str


class LoginSerializer(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str = ""
    token_type: str = "bearer"


class Detail(BaseModel):
    detail: str = ""
