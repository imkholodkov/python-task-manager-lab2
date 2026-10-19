"""ORM-модели.

Задание, шаг 6: модели в стиле SQLAlchemy 2.0 — через Mapped и mapped_column,
связь «один пользователь — много задач» через relationship с back_populates.
Поля — по таблице сущностей из раздела 2 задания.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, false, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    # Задание: id (PK).
    id: Mapped[int] = mapped_column(primary_key=True)
    # Задание: email уникальный.
    # Сверх задания: длина 320 — максимальная длина email по RFC 5321.
    email: Mapped[str] = mapped_column(String(320), unique=True)
    # Сверх задания: длина 100 — в задании длина name не задана.
    name: Mapped[str] = mapped_column(String(100))
    # Задание: created_at. Значение проставляет сама БД (DEFAULT now()),
    # время хранится с часовым поясом.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Задание, шаг 6: связь с задачами, парная к Task.owner.
    tasks: Mapped[list["Task"]] = relationship(back_populates="owner")


class Task(Base):
    __tablename__ = "tasks"

    # Задание: id (PK).
    id: Mapped[int] = mapped_column(primary_key=True)
    # Задание: title 1–200 символов. Верхняя граница — в БД (VARCHAR(200)),
    # нижняя проверяется в Pydantic-схеме.
    title: Mapped[str] = mapped_column(String(200))
    # Задание: description необязательно — колонка допускает NULL.
    description: Mapped[str | None] = mapped_column(Text)
    # Задание: done (bool, по умолчанию false) — значение по умолчанию и в Python,
    # и в БД.
    done: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    # Задание: created_at.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Задание: owner_id (FK User).
    # Сверх задания: index=True — индекс ускоряет фильтр GET /tasks?owner_id=...
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # Задание, шаг 6: связь с владельцем, парная к User.tasks.
    owner: Mapped["User"] = relationship(back_populates="tasks")
