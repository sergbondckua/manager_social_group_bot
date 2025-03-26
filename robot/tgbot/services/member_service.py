import logging
from typing import Any, List, Dict

from aiogram import types
from aiogram.types import FSInputFile

from common.utils import clean_tag_message
from core.settings import ADMINS_BOT
from profiles.models import ClubUser
from robot.models import DeepLink
from robot.tgbot.text.member_template import msg_press_pay_button

logger = logging.getLogger("robot")


async def get_or_create_user(
    telegram_id: int, defaults: dict
) -> tuple[ClubUser, bool]:
    """Повертає користувача з Telegram ID або створює нового."""
    return await ClubUser.objects.aget_or_create(
        telegram_id=telegram_id, defaults=defaults
    )


async def get_user_or_error(
    user_id: int, message: types.Message
) -> ClubUser | None:
    """Отримання користувача з бази даних з обробкою помилок"""
    try:
        return await ClubUser.objects.aget(telegram_id=user_id)
    except ClubUser.DoesNotExist:
        logger.error(f"Користувача {user_id} не знайдено")
        await message.answer(
            "❌ Помилка профілю. Зверніться до адміністратора."
        )
        return None


async def get_required_fields(
    user: ClubUser, field_configs: List[Dict]
) -> List[Dict]:
    """Фільтрація полів, які потребують заповнення.
    Використовує FIELD_CONFIGS для визначення обов'язкових полів.
    """
    return [
        config
        for config in field_configs
        if not getattr(user, config["name"])  # Перевіряємо, чи поле порожнє
    ]


async def update_user_field(user: ClubUser, field: str, value: Any):
    """Оновлює поля даних користувача."""
    setattr(user, field, value)
    await user.asave()


async def is_not_profile_complete(
    user: ClubUser, field_configs: List[Dict]
) -> bool:
    """Перевіряє, чи всі поля даних користувача заповнені."""
    required_fields = [
        not getattr(user, config["name"]) for config in field_configs
    ]
    return any(required_fields)


async def fetch_user_photo(message: types.Message) -> str | None:
    """Отримує ID фото профілю користувача."""
    try:
        photos = await message.bot.get_user_profile_photos(
            message.from_user.id
        )
        if photos.total_count > 0 and photos.photos[0]:
            return photos.photos[0][-1].file_id
    except Exception as e:
        logger.warning(
            "Не вдалося отримати фото користувача %s: %s",
            message.from_user.id,
            e,
        )
    return None


def prepare_user_data(message: types.Message, photo_id: str | None) -> dict:
    """Формує словник з даними користувача."""
    return {
        "username": message.from_user.username,
        "telegram_id": message.from_user.id,
        "telegram_first_name": message.from_user.first_name,
        "telegram_last_name": message.from_user.last_name,
        "telegram_username": message.from_user.username,
        "telegram_photo_id": photo_id,
        "telegram_language_code": message.from_user.language_code,
    }


async def process_deep_link(
    message: types.Message, deep_link_param: str
) -> None:
    """Обробляє deep link і відправляє повідомлення користувачу."""
    try:
        # Пошук об'єкта DeepLink у базі даних
        deep_link_instance = await DeepLink.objects.filter(
            command=deep_link_param
        ).afirst()
        if not deep_link_instance:
            await message.answer("Deep link не знайдено або він недійсний.")
            return

        # Форматування тексту повідомлення
        msg = clean_tag_message(deep_link_instance.text).format(
            user_id=message.from_user.id,
            full_name=message.from_user.full_name or "Користувач",
            first_name=message.from_user.first_name or "",
            last_name=message.from_user.last_name or "",
            username=message.from_user.username or "",
            today=message.date.strftime("%d.%m.%Y"),
            current_month=message.date.strftime("%B-%Y").upper(),
        )

        # Відправка фото або тексту
        if deep_link_instance.image:
            await message.answer_photo(
                photo=FSInputFile(deep_link_instance.image.path),
                caption=msg[:1024],
                show_caption_above_media=True,
            )
        else:
            await message.answer(msg[:4096])

        # Сповіщення адміністраторам що користувач натиснув посилання
        for admin in ADMINS_BOT:
            await message.bot.send_message(
                chat_id=admin,
                text=msg_press_pay_button.format(
                    full_name=message.from_user.full_name,
                    user_id=message.from_user.id,
                ),
            ) if message.from_user.id not in ADMINS_BOT else None

    except DeepLink.DoesNotExist:
        await message.answer("Deep link не знайдено або він недійсний.")
    except KeyError as e:
        await message.answer(
            f"Сталася помилка у форматуванні повідомлення: {e}"
        )
    except Exception as e:
        await message.answer(f"Сталася несподівана помилка: {e}")
