"""Подключение к базе данных.

Задание, шаг 5: асинхронный движок, фабрика сессий и зависимость get_session,
которая отдаёт сессию через yield.
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# Задание, шаг 5: асинхронный движок (драйвер asyncpg задаётся в DATABASE_URL:
# postgresql+asyncpg://...).
engine = create_async_engine(settings.database_url)

# Задание, шаг 5: фабрика сессий.
# Сверх задания: expire_on_commit=False — после commit атрибуты объектов не сбрасываются,
# и их можно читать без повторного запроса к БД (в async-режиме ленивая догрузка
# атрибутов вне await вызвала бы ошибку).
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


# Задание, шаг 1 (db.py: «движок, сессия, Base»): базовый класс для ORM-моделей.
# Его metadata используется Alembic для autogenerate (шаг 9).
class Base(DeclarativeBase):
    pass


# Задание, шаг 5: зависимость FastAPI. Сессия создаётся на каждый запрос
# и закрывается после ответа благодаря async with + yield.
async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
