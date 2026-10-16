"""Настройки приложения.

Задание, шаг 4: строка подключения к БД не хранится в коде, а читается
из переменной окружения DATABASE_URL через pydantic-settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Сверх задания: кроме переменной окружения, значение читается из файла .env
    # в корне проекта — так не нужно экспортировать DATABASE_URL перед каждым запуском.
    # Переменная окружения имеет приоритет над .env.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Задание, шаг 4: поле без значения по умолчанию — если DATABASE_URL не задан,
    # приложение не стартует (ValidationError), а не подключается к «зашитой» базе.
    database_url: str


settings = Settings()
