import logging
from typing import Any, List, Dict

from aiogram import types

from profiles.models import ClubUser

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
