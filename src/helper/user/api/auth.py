from fastapi import APIRouter, HTTPException, Query, Response, status

from src.helper import authenticate_user, login, logout
from src.helper.scheme import Detail, LoginSerializer, Token
from src.helper.user import User, UserCreateScheme

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_router(
    credentials: LoginSerializer, response: Response, next: str = Query(None)
):
    if user := await authenticate_user(credentials.username, credentials.password):
        return await login(user, response)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
    )


@router.post("/register", response_model=Token)
async def register_router(user: UserCreateScheme, response: Response):
    try:
        user = await User.create(**user.model_dump())
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    return await login(user, response)


@router.get("/logout", response_model=Detail)
async def logout_router(response: Response):
    return await logout(response)
