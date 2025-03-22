from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile

from common.utils import clean_tag_message
from profiles.models import ClubUser
from robot.models import DeepLink
from robot.tgbot.filters.member import ClubMemberFilter
from robot.tgbot.text.member_template import msg_handle_start

# Ініціалізація роутера
member_router = Router()
member_router.message.filter(ClubMemberFilter())


# Об'єднаний обробник команди /start
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

    # Спроба знайти або створити користувача
    user, created = await ClubUser.objects.aget_or_create(
        telegram_id=message.from_user.id, defaults=user_data
    )

    if not created:
        # Оновлюємо інформацію про користувача, якщо він вже існує
        for field, value in user_data.items():
            setattr(user, field, value)
        await user.asave()

    is_full_data = all([user.data_of_birth, user.phone_number])

    if is_full_data and not deep_link_param:
        await message.answer(
            f"Вітаю з поверненням, {message.from_user.first_name}!"
        )
    elif not is_full_data:
        await message.answer(
            msg_handle_start.format(name=message.from_user.first_name)
        )

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

        if not deep_link_instance:
            await message.answer("Deep link не знайдено або він недійсний.")
            return

        try:
            msg = clean_tag_message(deep_link_instance.text).format(
                user_id=message.from_user.id,
                full_name=message.from_user.full_name or "Користувач",
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
