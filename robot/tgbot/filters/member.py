from aiogram.filters import Filter
from aiogram.client.bot import Bot
from aiogram.types import TelegramObject, User
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError
from core.settings import DEFAULT_CHAT_ID


class ClubMemberFilter(Filter):
    """Фільтр перевіряє, чи є користувач учасником клубу."""

    def __init__(self, chat_id: int = DEFAULT_CHAT_ID):
        self.chat_id = chat_id

    async def __call__(self, obj: TelegramObject, bot: Bot) -> bool:
        user: User = obj.from_user

        if not user:
            return False

        try:
            member = await bot.get_chat_member(self.chat_id, user.id)
            return member.status in {"member", "administrator", "creator"}
        except (TelegramBadRequest, TelegramAPIError):
            return False
