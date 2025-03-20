import asyncio
import logging

from asgiref.sync import sync_to_async
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from common.resources.bot_msg_templates import greeting_text
from common.utils import get_random_greeting, get_random_birthday_sticker
from profiles.models import ClubUser
from robot.config import ROBOT
from robot.service.extend import TelegramService

logger = logging.getLogger("common")


@shared_task(expires=86399)
def send_birthday_greetings():
    """Завдання Celery для надсилання вітання іменинникам."""

    today = timezone.localtime(timezone.now()).date()

    @sync_to_async
    def fetch_users():
        return list(
            ClubUser.objects.filter(
                data_of_birth__day=today.day,
                data_of_birth__month=today.month,
                is_active=True,
            )
        )

    async def format_user_display_name(
        user: ClubUser, telegram_service: TelegramService
    ) -> str:
        """Форматує ім'я користувача для відображення."""

        # Отримуємо дані з Telegram
        username, telegram_full_name = (
            await telegram_service.get_username_and_fullname(user.telegram_id)
        )

        # Локальне повне ім'я користувача, якщо воно задане
        local_full_name = (
            f"{user.first_name} {user.last_name}".strip()
            if user.first_name and user.last_name
            else ""
        )

        # Форматування Telegram username
        formatted_username = f"(@{username})" if username else ""

        # Повертаємо відформатоване ім'я
        if local_full_name:
            return f"{local_full_name} {formatted_username}".strip()
        return f"{telegram_full_name} {formatted_username}".strip()

    async def main():
        users = await fetch_users()

        if not users:
            logger.info("Сьогодні іменинники відсутні.")
            return

        greeting = sync_to_async(get_random_greeting)()

        async with ROBOT as bot:
            sender = TelegramService(bot)
            for user in users:
                try:
                    # Отримуємо фото і відображуване ім'я користувача
                    photo = await sender.get_user_profile_photo(
                        user.telegram_id
                    )
                    name = await format_user_display_name(user, sender)

                    # Формуємо текст привітання
                    message = greeting_text.format(
                        today=today.strftime("%d.%m.%Y"),
                        name=name,
                        greeting=await greeting,
                    )
                    # Відправляємо привітання
                    await sender.send_message(
                        chat_ids=[settings.DEFAULT_CHAT_ID],
                        message=message,
                        photo=photo,
                        above_media=True,
                    )
                    # Відправляємо наліпку до привітання
                    await bot.send_sticker(
                        chat_id=settings.DEFAULT_CHAT_ID,
                        sticker=get_random_birthday_sticker(),
                    )
                    logger.info(
                        "Привітання успішно відправлено для користувача %s",
                        name,
                    )
                except Exception as error:
                    logger.error(
                        "Помилка при відправленні привітання для користувача %s: %s",
                        name,
                        error,
                    )

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except Exception as e:
        logger.error("Помилка виконання основного циклу asyncio: %s", e)
