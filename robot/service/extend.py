import logging
from typing import List, Optional

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from common.utils import clean_tag_message
from core.settings import DEFAULT_CHAT_ID

logger = logging.getLogger("robot")


class TelegramService:
    """Клас для відправлення повідомлень в Telegram"""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_message(
        self, message: str, chat_ids: List[int], photo: Optional[str] = None
    ) -> bool:
        """
        Відправляє повідомлення в зазначені чати
        Повертає статус відправлення (True/False)
        """
        if not chat_ids:
            return False

        success = False
        for chat_id in chat_ids:
            try:
                if photo:
                    await self.bot.send_chat_action(
                        chat_id=chat_id, action="upload_photo"
                    )
                    await self.bot.send_photo(
                        chat_id=chat_id,
                        photo=photo,
                        caption=clean_tag_message(message)[:1024],
                        parse_mode="HTML",
                    )
                else:
                    await self.bot.send_chat_action(
                        chat_id=chat_id, action="typing"
                    )
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=clean_tag_message(message)[:4096],
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                    )
                success = True
            except TelegramAPIError as e:
                logger.error(
                    "Помилка відправлення повідомлення для %s: %s", chat_id, e
                )
        return success

    async def get_user_profile_photo(self, user_id: int) -> Optional[str]:
        """Отримує фото профілю користувача"""

        photos = await self.bot.get_user_profile_photos(user_id)
        if photos.total_count > 0:
            # Отримуємо перше фото (найбільшого розміру)
            photo = photos.photos[0][-1]
            file_id = photo.file_id
            return file_id
        else:
            return None

    async def is_user_in_group(
        self, user_id: int, group_id: int = DEFAULT_CHAT_ID
    ) -> bool:
        """Перевіряє, чи є користувач учасником групи."""

        try:
            member = await self.bot.get_chat_member(group_id, user_id)
            return member.status in {"member", "administrator", "creator"}
        except TelegramAPIError as e:
            logger.error(
                "Помилка при отриманні статусу користувача %d у групі %d: %s",
                user_id,
                group_id,
                e,
            )
            return False

    # Функція для отримання інформації про користувача
    async def get_user_full_name(self, user_id: int) -> str:
        try:
            user = await self.bot.get_chat(user_id)
            return  user.full_name
        except Exception as e:
            logger.error(
                "Помилка при отриманні інформацією про користувача: %s", e
            )
            return ""
