"""Точка входа приложения.

Задание, шаг 1: создание приложения и подключение роутеров.
Задание, шаг 10: middleware Starlette — заголовок X-Process-Time и лог запросов.
Запуск (шаг 11): uvicorn app.main:app --reload
"""

import logging
import time

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.routers import tasks, users

# Сверх задания: настройка логирования уровня INFO с временем и именем логгера —
# без неё сообщения middleware не выводились бы в консоль.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("app.requests")


# Задание, шаг 10: middleware на базе Starlette (BaseHTTPMiddleware).
class ProcessTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        # Задание: заголовок X-Process-Time в ответе (время в секундах).
        response.headers["X-Process-Time"] = f"{elapsed:.4f}"
        # Задание: в лог пишутся метод, путь, статус и время обработки (в мс).
        logger.info(
            "%s %s %s %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed * 1000,
        )
        return response


# Задание, шаг 1: создание приложения.
app = FastAPI(title="Task Manager")
# Задание, шаг 10: подключение middleware.
app.add_middleware(ProcessTimeMiddleware)
# Задание, шаг 1 и 8: подключение роутеров.
app.include_router(users.router)
app.include_router(tasks.router)
