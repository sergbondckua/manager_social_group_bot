import asyncio
import logging
import os
import re

from aiogram import types
from aiogram.types import FSInputFile
from celery.result import AsyncResult


logger = logging.getLogger("robot")


async def wait_for_task_completion(
    task_id: str, file_name: str, status_message: types.Message
) -> str:
    """Очікування завершення задачі Celery з періодичним оновленням статусу"""
    max_wait_time = 300  # 5 хвилин
    wait_interval = 2  # перевіряємо кожні 2 секунди
    total_waited = 0

    while total_waited < max_wait_time:
        # Отримуємо результат задачі
        task_result = AsyncResult(task_id)

        # Перевіряємо статус
        if task_result.ready():
            if task_result.successful():
                return task_result.get()  # Отримуємо шлях до зображення
            else:
                # Отримуємо деталі помилки
                error = task_result.result
                raise Exception(f"Помилка візуалізації: {str(error)}")

        # Почекаємо перед наступною перевіркою
        await asyncio.sleep(wait_interval)
        total_waited += wait_interval

        # Оновлюємо повідомлення кожні 10 секунд
        if total_waited % 10 == 0:
            try:
                await status_message.edit_text(
                    f"GPX-файл '{file_name}' обробляється... ({total_waited} сек.)"
                )
            except Exception:
                pass  # Ігноруємо помилки при редагуванні

    # Якщо час вийшов
    raise TimeoutError(
        f"Візуалізація не завершилася за {max_wait_time} секунд"
    )


async def send_visualization_results(
    message: types.Message,
    gpx_path: str,
    image_path: str,
    original_filename: str,
) -> None:
    """Відправка результатів візуалізації"""

    # Підготовка файлів
    gpx_file = FSInputFile(gpx_path, filename=original_filename)
    image_file = FSInputFile(image_path, filename=os.path.basename(image_path))
    sanitized_filename = re.sub(r'\W', '', original_filename)  # Очищаємо ім'я файлу

    # Відправка зображення з підписом
    await message.bot.send_chat_action(message.chat.id, "upload_photo")
    caption = (f"Візуалізація маршруту '{original_filename}'\n\n"
               f"#неділя #треки #маршрут #{sanitized_filename}")
    await message.answer_photo(photo=image_file, caption=caption)

    # Відправка GPX файлу
    # await message.bot.send_chat_action(message.chat.id, "upload_document")
    # await message.answer_document(
    #     document=gpx_file, caption=f"#{sanitized_filename}"
    # )


def cleanup_files(file_paths: list) -> None:
    """Безпечне видалення файлів"""
    for path in file_paths:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            logger.warning("Не вдалося видалити файл %s: %s", path, e)
