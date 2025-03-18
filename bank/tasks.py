import asyncio
import logging
from typing import List, NoReturn, Tuple, Optional

from django.conf import settings
from celery import shared_task

from bank.models import MonoBankClient
from bank.services.mono import MonobankService
from robot.config import ROBOT
from robot.service.extend import TelegramService

logger = logging.getLogger("monobank")


@shared_task(expires=60 * 60)
def create_monobank_webhooks() -> NoReturn:
    """Celery-завдання для налаштування вебхуків усіх клієнтів MonoBank."""

    if not hasattr(settings, "BASE_URL"):
        logger.error("BASE_URL не встановлено в налаштуваннях")
        return

    webhook_path = settings.MONOBANK_WEBHOOK_PATH
    webhook_url = f"{settings.BASE_URL}{webhook_path}"
    active_clients = MonoBankClient.objects.filter(is_active=True)
    total_clients = active_clients.count()
    clients_iterator = active_clients.iterator()

    if not total_clients:
        logger.info("Немає клієнтів для налаштування вебхуків")
        return

    logger.info("Початок налаштування вебхуків для %s клієнтів", total_clients)

    success_count, failure_count = 0, 0
    for client in clients_iterator:
        if MonobankService(client.client_token).setup_webhook(webhook_url):
            logger.info(
                "Webhook успішно налаштовано для клієнта %s", client.name
            )
            success_count += 1
        else:
            logger.error(
                "Помилка налаштування webhook для клієнта %s", client.name
            )
            failure_count += 1

    logger.info(
        "Налаштування завершено. Успішно: %s/%s, Помилки: %s",
        success_count,
        total_clients,
        failure_count,
    )


@shared_task(expires=(24 * 60 * 60) * 28)
def send_telegram_message(
    message: str, chat_ids: List[int], payer_user_id: Optional[int] = None
) -> NoReturn:
    """
    Завдання Celery для надсилання повідомлення.

    :param message: текст повідомлення
    :param chat_ids: список чатів, до яких треба надіслати повідомлення
    :param payer_user_id: user_id платника (необов'язковий)
    """

    async def get_payer_details(
        user_id: int, sender
    ) -> Tuple[Optional[str], str, str]:
        """
        Отримує фото профілю та повне ім'я платника.

        :param user_id: Telegram user_id платника
        :param sender: TelegramService інстанс для взаємодії з API
        :return: Кортеж (фото, повне ім'я)
        """
        try:
            photo = await sender.get_user_profile_photo(user_id)
            full_name, username = await sender.get_username_and_fullname(
                user_id
            )
            return photo, full_name, username
        except Exception as e:
            logger.warning("Не вдалося отримати дані платника: %s", e)
            return None, "", ""

    async def main() -> None:
        async with ROBOT as bot:
            sender = TelegramService(bot)

            # Отримуємо дані платника, якщо user_id передано
            photo_payer, full_name, username = None, "", ""
            if payer_user_id:
                photo_payer, full_name, username = await get_payer_details(
                    payer_user_id, sender
                )

            # Форматуємо повідомлення
            formatted_username = f"{full_name} (@{username})" if username else ""
            display_name = formatted_username or full_name
            formatted_message = (
                message.format(name=display_name) if payer_user_id else message
            )

            # Логування для перевірки формату повідомлення
            logger.debug("Надсилається повідомлення: %s", formatted_message)

            # Надсилання повідомлення
            try:
                await sender.send_message(
                    formatted_message, chat_ids, photo_payer
                )
                logger.info("Повідомлення успішно надіслано")
            except Exception as e:
                logger.error("Помилка під час надсилання повідомлення: %s", e)

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except Exception as e:
        logger.error("Помилка виконання основного циклу asyncio: %s", e)
