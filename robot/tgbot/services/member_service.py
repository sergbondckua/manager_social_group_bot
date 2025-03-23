from typing import Any

from profiles.models import ClubUser


async def get_or_create_user(
    telegram_id: int, defaults: dict
) -> tuple[ClubUser, bool]:
    """Повертає користувача з Telegram ID або створює нового."""
    return await ClubUser.objects.aget_or_create(
        telegram_id=telegram_id, defaults=defaults
    )


async def update_user_field(user: ClubUser, field: str, value: Any):
    """Оновлює поля даних користувача."""
    setattr(user, field, value)
    await user.asave()


async def is_profile_complete(user: ClubUser) -> bool:
    """ Перевіряє, чи всі поля даних користувача заповнені. """
    return all([user.data_of_birth, user.phone_number])
