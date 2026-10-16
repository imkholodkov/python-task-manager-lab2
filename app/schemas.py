"""Pydantic-схемы.

Задание, шаг 7: для каждой сущности отдельные схемы *Create, *Read и *Update;
в *Update все поля необязательны; в *Read включено from_attributes=True;
для email используется тип EmailStr (требует пакет email-validator).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# Сверх задания: запрет явного null в Update-схемах для полей с NOT NULL в БД.
# Поле можно не передавать вовсе, но {"title": null} вернёт 422, а не 500
# от базы данных. Валидатор не срабатывает, если поле не передано.
def _not_null(value):
    if value is None:
        raise ValueError("field cannot be null")
    return value


# ---------- User ----------

# Задание, шаг 7: схема входных данных для POST /users.
class UserCreate(BaseModel):
    email: EmailStr
    # Сверх задания: ограничения длины name (1–100) — в задании не заданы.
    name: str = Field(min_length=1, max_length=100)


# Задание, шаг 7: Update-схема пользователя — все поля необязательны.
# Эндпоинта для обновления пользователя в задании нет, схема создана по требованию
# шага 7 «для каждой сущности».
class UserUpdate(BaseModel):
    email: EmailStr | None = None
    name: str | None = Field(default=None, min_length=1, max_length=100)

    # Сверх задания: см. _not_null выше.
    _check_not_null = field_validator("email", "name")(_not_null)


# Задание, шаг 7: схема ответа. from_attributes=True позволяет строить схему
# напрямую из ORM-объекта User.
class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    name: str
    created_at: datetime


# ---------- Task ----------

# Задание, шаг 7: схема входных данных для POST /tasks.
class TaskCreate(BaseModel):
    # Задание: title 1–200 символов.
    title: str = Field(min_length=1, max_length=200)
    # Задание: description необязательно.
    description: str | None = None
    # Задание: done по умолчанию false.
    done: bool = False
    owner_id: int


# Задание, шаг 7: Update-схема задачи для PATCH /tasks/{id} — все поля необязательны.
class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    # description можно сбросить явным null — колонка допускает NULL.
    description: str | None = None
    done: bool | None = None

    # Сверх задания: см. _not_null выше.
    _check_not_null = field_validator("title", "done")(_not_null)


# Задание, шаг 7: схема ответа с from_attributes=True.
class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    done: bool
    created_at: datetime
    owner_id: int
