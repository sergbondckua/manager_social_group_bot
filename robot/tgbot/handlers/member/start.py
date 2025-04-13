import asyncio
import os
from pathlib import Path

import logging
from aiogram import types, Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile
from celery.result import AsyncResult
from django.conf import settings

from robot.config import ROBOT
from robot.services.gpx_vizualizer import GPXVisualizer
from robot.tasks import visualize_gpx
from robot.tgbot.filters.member import ClubMemberFilter
from robot.tgbot.handlers.member.profile_field_configs import field_configs
from robot.tgbot.keyboards.member import yes_no_keyboard
from robot.tgbot.services.gpx_process_service import (
    wait_for_task_completion,
    cleanup_files,
    send_visualization_results,
)
from robot.tgbot.services.member_service import (
    get_or_create_user,
    update_user_field,
    is_not_profile_complete,
    fetch_user_photo,
    prepare_user_data,
    process_deep_link,
)
from robot.tgbot.text.member_template import msg_handle_start

logger = logging.getLogger("robot")

member_router = Router()
member_router.message.filter(ClubMemberFilter())


@member_router.message(CommandStart())
async def handle_start(message: types.Message, command: types.BotCommand):
    """Обробка команди /start з підтримкою deep link."""

    # Отримуємо аргумент deep link з команди
    deep_link_param = command.args
    # Отримуємо фото користувача
    photo = await fetch_user_photo(message)
    # Дані користувача
    user_data = prepare_user_data(message)
    # Отримуємо / створюємо користувача
    user, created = await get_or_create_user(
        message.from_user.id, user_data, photo
    )

    if not created:
        # Оновлюємо інформацію про користувача, якщо він вже існує
        for field, value in user_data.items():
            await update_user_field(user, field, value, photo)

    # Якщо deep link параметр вказаний
    if deep_link_param:
        await process_deep_link(message, deep_link_param)

    # Відповідь користувачу залежно від того, якщо в профілі вже заповнені дані або ні
    if await is_not_profile_complete(user, field_configs):
        await message.answer(
            msg_handle_start.format(name=message.from_user.first_name),
            reply_markup=yes_no_keyboard(),
        )
    else:
        await message.answer(f"Вітаю, {message.from_user.first_name}!")


@member_router.message(F.document.file_name.endswith(".gpx"))
async def handle_gpx_file(message: types.Message, bot: Bot = ROBOT):
    """ Обробка GPX-файлу. """
    try:
        # Отримуємо інформацію про GPX-файл
        document = message.document
        file_name = document.file_name
        file_id = document.file_id

        # Шлях для збереження GPX-файлу, створюємо директорію якщо вона не існує
        save_path = os.path.join(settings.MEDIA_ROOT, "gpx")
        Path(save_path).mkdir(parents=True, exist_ok=True)

        # Шлях для збереження файлу
        file_path = os.path.join(save_path, file_name)

        # Завантажуємо файл
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, destination=file_path)

        # Перевіряємо завантаження файлу
        if not os.path.exists(file_path):
            return await message.bot.send_message(
                settings.ADMINS_BOT[0],
                f"Помилка: GPX-файл не знайдено за шляхом {file_path}",
            )

        file_size = os.path.getsize(file_path)
        # Надсилаємо повідомлення про обробку файлу
        processing_msg = await message.answer(
            f"GPX-файл '{file_name}' завантажено ({file_size / 1024:.1f} КБ). "
            f"Обробляємо дані, це може зайняти деякий час..."
        )

        # Запускаємо задачу
        task = visualize_gpx.delay(file_path)

        try:
            # Очікуємо завершення задачі
            image_path = await wait_for_task_completion(
                task.id, file_name, processing_msg
            )

            # Перевіряємо завантаження зображення
            if not os.path.exists(image_path):
                raise FileNotFoundError(
                    f"Файл зображення не знайдено: {image_path}"
                )

            # Видаляємо службові повідомлення
            await processing_msg.delete()
            await message.delete()

            # Відправляємо результати
            await send_visualization_results(
                message, file_path, image_path, file_name
            )

            # Прибираємо за собою
            cleanup_files([image_path, file_path])

        except Exception as task_error:
            # Обробка помилок задачі
            error_msg = f"Помилка при обробці GPX-файлу: {str(task_error)}"
            logger.error(
                "Помилка обробки GPX-файлу: %s", error_msg, exc_info=task_error
            )
            await processing_msg.edit_text(error_msg)
            cleanup_files([file_path])
    except Exception as e:
        logger.error("Загальна помилка обробника GPX-файлу: %s", e)
        await message.bot.send_message(
            settings.ADMINS_BOT[0], f"Помилка при обробці файлу: {str(e)}"
        )
