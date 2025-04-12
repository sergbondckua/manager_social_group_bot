import os
from pathlib import Path

from aiogram import types, Router, F, Bot
from aiogram.filters import CommandStart
from django.conf import settings

from robot.config import ROBOT
from robot.services.gpx_vizualizer import GPXVisualizer
from robot.tasks import visualize_gpx
from robot.tgbot.filters.member import ClubMemberFilter
from robot.tgbot.handlers.member.profile_field_configs import field_configs
from robot.tgbot.keyboards.member import yes_no_keyboard
from robot.tgbot.services.member_service import (
    get_or_create_user,
    update_user_field,
    is_not_profile_complete,
    fetch_user_photo,
    prepare_user_data,
    process_deep_link,
)
from robot.tgbot.text.member_template import msg_handle_start

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
    # Отримуємо інформацію про файл
    try:
        document = message.document
        file_name = document.file_name
        file_id = document.file_id

        # Використовуємо pathlib для створення директорії
        Path(settings.MEDIA_ROOT, "gpx").mkdir(parents=True, exist_ok=True)

        # Шлях для збереження файлу
        file_path = os.path.join(settings.MEDIA_ROOT, "gpx", file_name)

        # Завантажуємо файл
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, destination=file_path)

        # Перевіряємо, чи файл збережено
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            await message.answer(
                f"GPX-файл '{file_name}' успішно збережено! Розмір: {file_size} байт"
            )
        else:
            await message.answer(
                f"Файл завантажено, але не знайдено за шляхом {file_path}"
            )

        # Обробка GPX-файлу і візуалізація маршруту за допомогою Celery
        visualize_gpx.delay(file_path)

    except Exception as e:
        # Детальна обробка помилок
        error_message = f"Помилка при обробці файлу: {str(e)}"
        await message.answer(error_message)
        return
