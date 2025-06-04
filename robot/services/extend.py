import logging
from typing import List, Optional, Tuple

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest

from common.utils import clean_tag_message
from core.settings import DEFAULT_CHAT_ID

logger = logging.getLogger("robot")


class TelegramService:
    """ Клас для відправлення повідомлень в Telegram. """

    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_message(
        self,
        message: str,
        chat_ids: List[int],
        photo: Optional[str] = None,
        above_media: bool = False,
    ) -> bool:
        """
        Відправляє повідомлення в зазначені чати
        Повертає статус відправлення (True/False)
        :param message: повідомлення
        :param chat_ids: список чатів
        :param photo: фото повідомлення
        :param above_media: відображати повідомлення над зображенням
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
                        protect_content=True,
                        show_caption_above_media=above_media,
                    )
                else:
                    await self.bot.send_chat_action(
                        chat_id=chat_id, action="typing"
                    )
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=clean_tag_message(message)[:4096],
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
    async def get_username_and_fullname(
        self, user_id: int
    ) -> Optional[Tuple[str, str]]:
        try:
            user = await self.bot.get_chat(user_id)
            username = user.username or ""
            return username, user.full_name
        except TelegramBadRequest as e:
            logger.warning(
                "Користувача %s не знайдено: %s",
                user_id,
                e,
            )
            return "", ""
        except Exception as e:
            logger.error(
                "Помилка при отриманні інформацією про користувача: %s", e
            )
            return "", ""
