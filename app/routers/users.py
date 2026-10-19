"""Эндпоинты пользователей.

Задание, шаг 8: роутер на APIRouter, сессия только через Depends(get_session),
ошибки через HTTPException с кодами из таблицы эндпоинтов задания:
  POST /users        — 201, 409 (email занят), 422
  GET  /users/{id}   — 200, 404
Код 422 FastAPI возвращает сам при ошибке валидации Pydantic-схемы.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import User
from app.schemas import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


# Задание: POST /users — создать пользователя.
# Сверх задания: параметр responses описывает код 409 в Swagger UI
# (FastAPI не выводит коды из HTTPException автоматически).
@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "Email already registered"}},
)
async def create_user(data: UserCreate, session: AsyncSession = Depends(get_session)):
    # Задание: 409, если email уже занят.
    exists = await session.scalar(select(User.id).where(User.email == data.email))
    if exists is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(**data.model_dump())
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as err:
        # Сверх задания: защита от гонки — параллельный запрос успел занять тот же
        # email между проверкой выше и вставкой; уникальный индекс в БД отклонит
        # вставку, и клиент получит 409, а не 500.
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered") from err
    # Перечитываем объект, чтобы получить id и created_at, проставленные БД.
    await session.refresh(user)
    return user


# Задание: GET /users/{id} — получить пользователя, 404 если нет.
# Сверх задания: responses описывает 404 в Swagger UI.
@router.get(
    "/{user_id}",
    response_model=UserRead,
    responses={404: {"description": "User not found"}},
)
async def get_user(user_id: int, session: AsyncSession = Depends(get_session)):
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user
