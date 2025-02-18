from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordBearer
from jwt import decode, encode
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from tortoise.exceptions import DoesNotExist

from src.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_HASH_ALGORITHM,
    REFRESH_SECRET_KEY,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SECRET_KEY,
)
from src.helper.user.model import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def authenticate_user(username: str, password: str) -> User | Literal[False]:
    try:
        user = await User.get(username=username)
    except DoesNotExist:
        return False
    if not user:
        return False
    if not user.verify_password(password):
        return False
    return user


async def create_access_token(user_id: int) -> str:
    expiration = datetime.now(tz=timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "exp": expiration,
        "iat": datetime.now(tz=timezone.utc),
        "id": user_id,
    }
    access_token = encode(payload, SECRET_KEY, algorithm=JWT_HASH_ALGORITHM)
    return access_token


async def create_refresh_token(user_id: int) -> str:
    expiration = datetime.now(tz=timezone.utc) + timedelta(
        days=REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "exp": expiration,
        "iat": datetime.now(tz=timezone.utc),
        "id": user_id,
    }
    refresh_token = encode(payload, REFRESH_SECRET_KEY, algorithm=JWT_HASH_ALGORITHM)
    return refresh_token


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = decode(
            token,
            SECRET_KEY,
            algorithms=[JWT_HASH_ALGORITHM],
            options={"verify_exp": True},
        )
        user = await User.get(id=payload.get("id"))
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    return user


async def login_required(request: Request, response: Response):
    access_token = request.cookies.get("access_token")
    if not access_token:
        return None
    try:
        user = await get_current_user(access_token)
    except ExpiredSignatureError:
        try:
            refresh_access_token(request.cookies.get("refresh_token"), response)
        except Exception as _:
            return None
    return user


async def refresh_access_token(
    refresh_token: str, response: Response
) -> dict[str, str]:
    try:
        payload = decode(
            refresh_token,
            REFRESH_SECRET_KEY,
            algorithms=[JWT_HASH_ALGORITHM],
            options={"verify_exp": True},
        )
        user = await User.get(id=payload.get("id"))
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    new_access_token = await create_access_token(user.id)

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=True,
        max_age=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        expires=datetime.now(tz=timezone.utc)
        + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        samesite="Strict",
    )

    return {"access_token": new_access_token, "token_type": "bearer"}


async def login(user: User, response: Response) -> dict[str, str]:
    access_token = await create_access_token(user.id)
    refresh_token = await create_refresh_token(user.id)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        max_age=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        expires=datetime.now(tz=timezone.utc)
        + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        samesite="Strict",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        max_age=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        expires=datetime.now(tz=timezone.utc)
        + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        samesite="Strict",
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


async def logout(response: Response):
    response.delete_cookie(
        key="access_token", secure=True, httponly=True, samesite="Strict"
    )
    response.delete_cookie(
        key="refresh_token", secure=True, httponly=True, samesite="Strict"
    )

    return {"detail": "Successfully logged out"}
