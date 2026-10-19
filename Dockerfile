# Практическая работа №3, шаг 5: многоэтапная сборка и запуск
# от непривилегированного пользователя.

# --- Этап 1: сборка зависимостей в отдельный venv ---
FROM python:3.12-slim AS builder

# Не хранить кэш pip и не проверять новую версию pip.
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
# Зависимости ставятся в отдельный venv — его целиком копирует второй этап.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Сначала только requirements.txt: слой с зависимостями кэшируется
# и не пересобирается, пока список зависимостей не изменился.
COPY requirements.txt .
RUN pip install -r requirements.txt

# --- Этап 2: финальный образ — только venv и код, без pip-кэша и сборочных файлов ---
FROM python:3.12-slim AS runtime

# Без .pyc-файлов, вывод Python сразу в лог; venv в PATH.
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/venv/bin:$PATH"

# Системный пользователь app без домашней папки и без пароля.
RUN groupadd --system app && useradd --system --gid app --no-create-home app

WORKDIR /app
# Из первого этапа берём только готовый venv.
COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app migrations ./migrations
COPY --chown=app:app app ./app

# Всё дальше — и сам сервис — выполняется от app, не от root.
USER app
EXPOSE 8000
# Слушать на всех интерфейсах, иначе сервис недоступен снаружи контейнера.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
