# Менеджер задач — FastAPI + PostgreSQL + SQLAlchemy + Pydantic

Практическая работа № 2: REST API для хранения пользователей и их задач.

Стек: FastAPI, Starlette (middleware), SQLAlchemy 2.0 (async, asyncpg), Pydantic v2, pydantic-settings, Alembic, PostgreSQL 16 в Docker.

## Требования

- Python 3.11+
- Docker и Docker Compose
- Git

## Запуск

1. Клонировать репозиторий и перейти в папку проекта:

   ```bash
   git clone https://github.com/imkholodkov/python-task-manager-lab2.git
   cd python-task-manager-lab2
   ```

2. Создать файл с переменными окружения из образца:

   ```bash
   cp .env.example .env
   ```

3. Запустить PostgreSQL и проверить доступность:

   ```bash
   docker compose up -d db
   docker compose exec db psql -U app -d tasks -c "select 1"
   ```

4. Создать виртуальное окружение и установить зависимости:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

5. Применить миграции (таблицы создаются только миграцией Alembic, `create_all` не используется):

   ```bash
   alembic upgrade head
   ```

6. Запустить сервис:

   ```bash
   uvicorn app.main:app --reload
   ```

7. Открыть Swagger UI: http://localhost:8000/docs

Остановка: `Ctrl+C` для сервиса, `docker compose stop` для базы. Данные сохраняются в томе `pgdata`.

## Структура проекта

```
app/
├── __init__.py
├── main.py          # создание приложения, middleware, подключение роутеров
├── config.py        # настройки (pydantic-settings), DATABASE_URL
├── db.py            # асинхронный движок, фабрика сессий, Base, get_session
├── models.py        # ORM-модели User и Task (SQLAlchemy 2.0)
├── schemas.py       # Pydantic-схемы Create / Read / Update
└── routers/
    ├── users.py     # /users
    └── tasks.py     # /tasks
migrations/          # Alembic (async), первая миграция в versions/
alembic.ini
docker-compose.yml   # PostgreSQL 16
requirements.txt
.env.example         # образец DATABASE_URL
```

## Эндпоинты

| Метод | Путь | Описание | Коды ответа |
|---|---|---|---|
| POST | /users | создать пользователя | 201, 409 (email занят), 422 |
| GET | /users/{id} | получить пользователя | 200, 404 |
| POST | /tasks | создать задачу | 201, 404 (нет владельца), 422 |
| GET | /tasks | список задач; фильтры `done`, `owner_id`; пагинация `limit` (1–100), `offset` | 200 |
| GET | /tasks/{id} | получить задачу | 200, 404 |
| PATCH | /tasks/{id} | частично обновить задачу | 200, 404, 422 |
| DELETE | /tasks/{id} | удалить задачу | 204, 404 |

Каждый ответ содержит заголовок `X-Process-Time` — время обработки запроса в секундах; метод, путь, статус и время пишутся в лог сервиса.

## Скриншоты

### Swagger UI

| Запрос | Скриншот |
|---|---|
| POST /users → 201 | ![](docs/screenshots/01-post-users-201.png) |
| GET /users/{id} → 200 | ![](docs/screenshots/02-get-user-200.png) |
| POST /tasks → 201 | ![](docs/screenshots/03-post-tasks-201.png) |
| GET /tasks → 200 | ![](docs/screenshots/04-get-tasks-200.png) |
| PATCH /tasks/{id} → 200 | ![](docs/screenshots/05-patch-task-200.png) |
| DELETE /tasks/{id} → 204 | ![](docs/screenshots/06-delete-task-204.png) |
| GET /tasks/{id} → 404 | ![](docs/screenshots/07-get-task-404.png) |

### Таблицы в БД (`\dt` в psql)

```bash
docker compose exec db psql -U app -d tasks -c '\dt'
```

![](docs/screenshots/08-dt.png)

## Ответы на контрольные вопросы

**1. Чем FastAPI отличается от Starlette и какие компоненты Starlette он использует?**

Starlette — лёгкий ASGI-фреймворк: маршрутизация, запросы и ответы, middleware, WebSocket, фоновые задачи, тестовый клиент. FastAPI построен поверх Starlette (класс `FastAPI` наследуется от `Starlette`) и добавляет: валидацию и сериализацию данных через Pydantic по аннотациям типов, систему зависимостей `Depends`, автоматическую генерацию OpenAPI-схемы и документации (Swagger UI, ReDoc). От Starlette FastAPI использует `Request`/`Response` и их подклассы, маршрутизацию, middleware (в этом проекте — для `X-Process-Time`), обработку исключений, `BackgroundTasks`, WebSocket, статические файлы и `TestClient`.

**2. Зачем разделять схемы Create, Read и Update?**

У каждой операции свой набор полей и свои правила. В Create клиент не передаёт `id` и `created_at` — их назначает сервер, а обязательные поля обязательны. Read описывает ответ: в нём есть серверные поля (`id`, `created_at`) и нет внутренних данных, которые не нужно отдавать. В Update все поля необязательны, чтобы PATCH мог изменить только часть полей. Одна общая схема либо требовала бы лишнее, либо пропускала бы недопустимое (например, позволила бы клиенту задать `id`).

**3. Что делает `from_attributes=True`?**

Разрешает Pydantic создавать модель из произвольного объекта, читая значения из его атрибутов (`obj.id`, `obj.title`), а не только из словаря. Благодаря этому обработчик может вернуть ORM-объект SQLAlchemy, а FastAPI преобразует его в схему `*Read` через `response_model`. В Pydantic v1 эта настройка называлась `orm_mode = True`.

**4. Почему сессия передаётся через Depends, а не создаётся глобально?**

Сессия SQLAlchemy не потокобезопасна и хранит состояние (идентичность объектов, открытую транзакцию), поэтому одна глобальная сессия на все параллельные запросы привела бы к смешению данных и ошибкам транзакций. `Depends(get_session)` создаёт отдельную сессию на каждый запрос и гарантированно закрывает её после ответа (код после `yield`). Кроме того, зависимость легко подменить в тестах через `app.dependency_overrides`.

**5. Чем `exclude_unset=True` отличается от `exclude_none=True`?**

`exclude_unset=True` исключает поля, которые клиент не передал в запросе, даже если у них есть значение по умолчанию. `exclude_none=True` исключает все поля со значением `None` — и непереданные, и переданные явно как `null`. Для PATCH нужен `exclude_unset`: тогда `{"description": null}` очистит описание, а непереданные поля не изменятся. С `exclude_none` явный `null` был бы проигнорирован, и сбросить поле в `NULL` стало бы невозможно.

**6. Почему в production таблицы не создают через `create_all`?**

`create_all` только создаёт отсутствующие таблицы и не изменяет существующие: добавить колонку, поменять тип, создать индекс в уже работающей базе он не может. У него нет истории изменений, версии схемы и отката. Миграции Alembic хранят каждое изменение схемы в отдельном файле под версией, применяются одинаково на всех окружениях (`alembic upgrade head`), проходят ревью вместе с кодом и умеют откатываться (`alembic downgrade`), сохраняя данные.

## Сделано сверх задания

В коде каждое дополнение помечено комментарием «Сверх задания».

| Где | Что |
|---|---|
| requirements.txt | `sqlalchemy[asyncio]` (ставит greenlet для async-режима), `email-validator` (нужен для `EmailStr`) |
| config.py | чтение `DATABASE_URL` из файла `.env` в дополнение к переменной окружения |
| db.py | `expire_on_commit=False` |
| models.py | длины `email` 320 и `name` 100, индекс на `tasks.owner_id` |
| schemas.py | запрет явного `null` для NOT NULL полей в Update-схемах (422 вместо 500), длина `name` 1–100 |
| routers/users.py | проверка email до вставки + перехват `IntegrityError` при гонке |
| routers/tasks.py | сортировка по `id` для стабильной пагинации, `limit` по умолчанию 20, `offset ≥ 0` |
| routers/*.py | коды 404 и 409 описаны в Swagger UI через `responses` |
| main.py | настройка `logging.basicConfig` |
| .gitignore | исключение `.venv`, `.env`, кэша и настроек IDE |
