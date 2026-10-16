"""Эндпоинты задач.

Задание, шаг 8: роутер на APIRouter, сессия только через Depends(get_session),
ошибки через HTTPException с кодами из таблицы эндпоинтов задания:
  POST   /tasks       — 201, 404 (нет владельца), 422
  GET    /tasks       — 200 (фильтры done, owner_id; пагинация limit 1–100, offset)
  GET    /tasks/{id}  — 200, 404
  PATCH  /tasks/{id}  — 200, 404, 422
  DELETE /tasks/{id}  — 204, 404
Код 422 FastAPI возвращает сам при ошибке валидации.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Task, User
from app.schemas import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])

# Сверх задания: описание кода 404 для Swagger UI, общее для эндпоинтов /tasks/{id}.
TASK_NOT_FOUND = {404: {"description": "Task not found"}}


# Сверх задания: вспомогательная функция, чтобы не повторять поиск задачи
# и выброс 404 в GET, PATCH и DELETE.
async def _get_task_or_404(task_id: int, session: AsyncSession) -> Task:
    task = await session.get(Task, task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return task


# Задание: POST /tasks — создать задачу; 404, если владельца нет.
# Сверх задания: responses описывает 404 в Swagger UI.
@router.post(
    "",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"description": "Owner not found"}},
)
async def create_task(data: TaskCreate, session: AsyncSession = Depends(get_session)):
    if await session.get(User, data.owner_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Owner not found")
    task = Task(**data.model_dump())
    session.add(task)
    await session.commit()
    # Перечитываем объект, чтобы получить id и created_at, проставленные БД.
    await session.refresh(task)
    return task


# Задание: GET /tasks — список с фильтрами done, owner_id и пагинацией.
@router.get("", response_model=list[TaskRead])
async def list_tasks(
    done: bool | None = None,
    owner_id: int | None = None,
    # Задание: limit от 1 до 100. Сверх задания: значение по умолчанию 20.
    limit: int = Query(20, ge=1, le=100),
    # Задание: offset. Сверх задания: запрет отрицательного значения (ge=0).
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    # Сверх задания: сортировка по id — без неё порядок строк в PostgreSQL
    # не гарантирован, и пагинация могла бы пропускать или дублировать задачи.
    query = select(Task).order_by(Task.id).limit(limit).offset(offset)
    if done is not None:
        query = query.where(Task.done == done)
    if owner_id is not None:
        query = query.where(Task.owner_id == owner_id)
    return (await session.scalars(query)).all()


# Задание: GET /tasks/{id} — получить задачу, 404 если нет.
@router.get("/{task_id}", response_model=TaskRead, responses=TASK_NOT_FOUND)
async def get_task(task_id: int, session: AsyncSession = Depends(get_session)):
    return await _get_task_or_404(task_id, session)


# Задание: PATCH /tasks/{id} — частичное обновление, 404 если нет, 422 при ошибке данных.
@router.patch("/{task_id}", response_model=TaskRead, responses=TASK_NOT_FOUND)
async def update_task(
    task_id: int, data: TaskUpdate, session: AsyncSession = Depends(get_session)
):
    task = await _get_task_or_404(task_id, session)
    # exclude_unset=True — берём только поля, которые клиент реально передал,
    # остальные поля задачи не трогаем.
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    await session.commit()
    await session.refresh(task)
    return task


# Задание: DELETE /tasks/{id} — удалить задачу, 204 без тела, 404 если нет.
@router.delete(
    "/{task_id}", status_code=status.HTTP_204_NO_CONTENT, responses=TASK_NOT_FOUND
)
async def delete_task(task_id: int, session: AsyncSession = Depends(get_session)):
    task = await _get_task_or_404(task_id, session)
    await session.delete(task)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
