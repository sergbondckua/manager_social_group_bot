from aiogram import types, Router
from aiogram.filters import CommandStart

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


@member_router.message(CommandStart())
async def handle_start(message: types.Message, command: types.BotCommand):
    """Обробка команди /start з підтримкою deep link."""

    # Отримуємо аргумент deep link з команди
    deep_link_param = command.args
    # Отримуємо фото користувача
    photo_id = await fetch_user_photo(message)
    # Дані користувача
    user_data = prepare_user_data(message, photo_id)
    # Отримуємо / створюємо користувача
    user, created = await get_or_create_user(message.from_user.id, user_data)

    if not created:
        # Оновлюємо інформацію про користувача, якщо він вже існує
        for field, value in user_data.items():
            await update_user_field(user, field, value)

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
        await message.answer(
            f"Вітаю, {message.from_user.first_name}!"
        )
