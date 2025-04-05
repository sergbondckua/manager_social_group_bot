#!/bin/bash
set -e

# Очікування готовності бази даних
if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
  echo "Waiting for database..."
  while ! nc -z $DB_HOST $DB_PORT; do
    sleep 0.1
  done
  echo "Database started"
fi

# Міграція бази даних (тільки для веб-сервісу)
if [[ "$*" == *"uvicorn"* ]]; then
  echo "Applying database migrations..."
  python manage.py migrate

  # Збирання статичних файлів
  echo "Collecting static files..."
  python manage.py collectstatic --noinput

  # Запуск бота
  echo "Starting bot..."
  python manage.py startbot
fi

# Запуск команди
exec "$@"