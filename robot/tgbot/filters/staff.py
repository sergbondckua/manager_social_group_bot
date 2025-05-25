from aiogram.filters import Filter
from aiogram.client.bot import Bot
from aiogram.types import TelegramObject, User
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError
from asgiref.sync import sync_to_async

from profiles.models import ClubUser


class ClubStaffFilter(Filter):
    """Фільтр перевіряє, чи є користувач модератором клубу."""

    @sync_to_async
    def get_staff_telegram_ids(self):
        """Асинхронен запит для отримання Telegram ID модераторів клубу."""
        return list(
            ClubUser.objects.filter(is_staff=True).values_list("telegram_id", flat=True)
        )

    async def __call__(self, obj: TelegramObject, bot: Bot) -> bool:
        user: User = obj.from_user

        if not user or not user.id:
            return False

        try:
            # Виклик асинхронної функції
            staff_telegram_ids = await self.get_staff_telegram_ids()
            return user.id in staff_telegram_ids
        except (TelegramBadRequest, TelegramAPIError):
            return False
