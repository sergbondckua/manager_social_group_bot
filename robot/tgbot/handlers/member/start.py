from aiogram import types, Router
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile

from common.utils import clean_tag_message
from robot.models import DeepLink
from robot.tgbot.keyboards.member import yes_no_keyboard
from robot.tgbot.services.member_service import (
    get_or_create_user,
    is_profile_complete,
    update_user_field,
)
from robot.tgbot.text.member_template import msg_handle_start

member_router = Router()


@member_router.message(CommandStart())
async def handle_start(message: types.Message, command: types.BotCommand):
    """Обробка команди /start з підтримкою deep link."""

    # Отримуємо аргумент deep link з команди
    deep_link_param = command.args

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
    user, created = await get_or_create_user(message.from_user.id, user_data)

    if not created:
        # Оновлюємо інформацію про користувача, якщо він вже існує
        for field, value in user_data.items():
            await update_user_field(user, field, value)

        # Якщо deep link параметр вказаний
        if deep_link_param:
            # Обробка deep link
            try:
                deep_link_instance = await DeepLink.objects.filter(
                    command=deep_link_param
                ).afirst()
            except Exception:
                await message.answer("Сталася помилка при обробці deep link.")
                return
            except DeepLink.DoesNotExist:
                await message.answer(
                    "Deep link не знайдено або він недійсний."
                )
                return

            try:
                msg = clean_tag_message(deep_link_instance.text).format(
                    user_id=message.from_user.id,
                    full_name=message.from_user.full_name or "Користувач",
                    first_name=message.from_user.first_name or "",
                    last_name=message.from_user.last_name or "",
                    username=message.from_user.username or "",
                    today=message.date.strftime("%d.%m.%Y"),
                    current_month=message.date.strftime("%B-%Y").upper(),
                )
                if deep_link_instance.image:
                    await message.answer_photo(
                        photo=FSInputFile(deep_link_instance.image.path),
                        caption=msg[:1024],
                        show_caption_above_media=True,
                    )
                else:
                    await message.answer(msg[:4096])
            except (KeyError, AttributeError):
                await message.answer(
                    "Сталася помилка у форматуванні повідомлення."
                )

        # Відповідь користувачу залежно від того, якщо в профілі вже заповнені дані або ні
        if not await is_profile_complete(user):
            await message.answer(
                msg_handle_start.format(name=message.from_user.first_name),
                reply_markup=yes_no_keyboard(),
            )
        else:
            await message.answer(
                f"Вітаю з поверненням, {message.from_user.first_name}!"
            )