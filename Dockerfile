FROM python:3.12.0-slim

# Метадані
LABEL authors="sergbondckua" \
      version="1.0" \
      description="Django application container"

# Вставляємо змінні середовища
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    MPLCONFIGDIR=/tmp/matplotlib

# Встановлюємо необхідні системні пакети
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    gettext \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Оболонка за замовчуванням bash
SHELL ["/bin/bash", "-c"]


# Визначаємо робочу директорію
WORKDIR /app

# Встановлюємо залежності окремо для кешування шару
RUN pip install --upgrade pip
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


# Створюємо директорії для статичних файлів та медіа з відповідними правами
RUN mkdir -p /app/static /app/media \
    && chmod -R 755 /app/static /app/media

# Копіюємо файли проекту
COPY . .

# Порт, на якому запускається додаток
EXPOSE 8000