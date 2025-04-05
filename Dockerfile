FROM python:3.12.0-slim

# Метадані
# Метадані
LABEL authors="sergbondckua" \
      version="1.0" \
      description="Django application container"

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