from aiogram import types, Router
from aiogram.filters import CommandStart
from robot.tgbot.keyboards.member import yes_no_keyboard
from robot.tgbot.services.member_service import (
    get_or_create_user,
    is_profile_complete,
)
from robot.tgbot.text.member_template import msg_handle_start

member_router = Router()


@member_router.message(CommandStart())
async def handle_start(message: types.Message):

    # Отримуємо фото користувача
    photos = await message.bot.get_user_profile_photos(message.from_user.id)
    photo_id = photos.photos[0][-1].file_id if photos.total_count > 0 else None

    # Дані користувача
    user_data = {
        "username": message.from_user.username,
        "telegram_id": message.from_user.id,
        "telegram_first_name": message.from_user.first_name,
        "telegram_last_name": message.from_user.last_name,
        "telegram_username": message.from_user.username,
        "telegram_photo_id": photo_id,
        "telegram_language_code": message.from_user.language_code,
    }
    user, _ = await get_or_create_user(message.from_user.id, user_data)

    if not await is_profile_complete(user):
        await message.answer(
            msg_handle_start.format(name=message.from_user.first_name),
            reply_markup=yes_no_keyboard(),
        )
    else:
        await message.answer(
            f"Вітаю з поверненням, {message.from_user.first_name}!"
        )
