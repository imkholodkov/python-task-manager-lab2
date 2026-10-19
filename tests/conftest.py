"""Тестовые фикстуры.

Практическая работа №3, шаг 3: тесты работают с отдельной БД tasks_test,
каждый тест начинается на чистых таблицах, зависимость get_session
подменяется через app.dependency_overrides.
"""

import os
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DATABASE_URL = os.environ.setdefault(
    "TEST_DATABASE_URL", "postgresql+asyncpg://app:app@localhost:5432/tasks_test"
)
# app.config читает DATABASE_URL при импорте — направляем и его на тестовую БД.
os.environ.setdefault("DATABASE_URL", TEST_DATABASE_URL)

from app import models  # noqa: E402, F401 — регистрирует таблицы в Base.metadata
from app.db import Base, get_session  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session_factory(engine):
    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
async def client(session_factory) -> AsyncIterator[AsyncClient]:
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def user(client):
    response = await client.post("/users", json={"email": "owner@example.com", "name": "Owner"})
    return response.json()
