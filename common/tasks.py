import asyncio
import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from common.utils import get_random_greeting, clean_tag_message
from profiles.models import ClubUser
from robot.config import ROBOT
from robot.service.extend import TelegramService

logger = logging.getLogger("common")


@shared_task
def send_birthday_greetings():
    today = timezone.now().date()
    users = ClubUser.objects.filter(
        data_of_birth__day=today.day,
        data_of_birth__month=today.month,
        is_active=True,
    )
    if not users.exists():
        logger.info("Сьогодні іменинники відсутні.")
        return

    greeting = clean_tag_message(get_random_greeting())

    async def get_display_name(user: ClubUser, sender: TelegramService) -> str:
        """
        Повертає відформатоване ім'я користувача.

        - Використовує локальні дані (`first_name`, `last_name`) або дані Telegram (`username`, `full_name`).
        - Форматує ім'я з посиланням на Telegram-username, якщо він доступний.
        """
        # Отримуємо дані з Telegram
        username, tg_full_name = await sender.get_username_and_fullname(
            user.telegram_id
        )

        # Локальне повне ім'я, якщо є
        full_name = (
            f"{user.first_name} {user.last_name}".strip()
            if user.first_name or user.last_name
            else ""
        )

        # Форматування Telegram username
        formatted_username = f"(@{username})" if username else ""

        # Повертаємо відформатоване ім'я
        return (
            f"{full_name} {formatted_username}".strip()
            or f"{tg_full_name} {formatted_username}".strip()
        )

    async def main():
        async with ROBOT as bot:
            sender = TelegramService(bot)
            for user in users:
                try:
                    # Отримуємо фото і відображуване ім'я користувача
                    photo = await sender.get_user_profile_photo(
                        user.telegram_id
                    )
                    name = await get_display_name(user, sender)

                    # Формуємо текст привітання
                    greeting_text = greeting_text.format(
                        today=today.strftime("%d.%m.%Y"),
                        name=name,
                        greeting=greeting,
                    )
                    # Відправляємо привітання
                    await sender.send_message(
                        chat_ids=[settings.DEFAULT_CHAT_ID],
                        message=greeting_text,
                        photo=photo,
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
