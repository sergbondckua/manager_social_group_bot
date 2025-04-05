FROM python:3.12.0-slim

# Метадані
LABEL authors="sergbondckua"
LABEL version="1.0"
LABEL description="Django application container"

# Оболонка за замовчуванням bash
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Вставляємо змінні середовища
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Встановлюємо необхідні системні пакети
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       gcc \
       postgresql-client \
       gettext \
       netcat-traditional \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Визначаємо робочу директорію
WORKDIR /app

# Встановлюємо залежності окремо для кешування шару
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Створюємо директорію для статичних файлів
RUN mkdir -p /app/static /app/media

# Копіюємо файли проекту
COPY . .

# Порт, на якому запускається додаток
EXPOSE 8000

# Entrypoint скрипт для запуску додатку
ENTRYPOINT ["/app/entrypoint.sh"]

# Команда за замовчуванням, яку буде перевизначено в docker-compose
CMD ["uvicorn", "core.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
