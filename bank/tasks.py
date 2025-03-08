import asyncio
import logging
from typing import List, NoReturn

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
    message: str, chat_ids: List[int], payer_user_id: int = None
) -> NoReturn:
    """
    Завдання Celery для надсилання повідомлення.
        param message: текст повідомлення
        param chat_ids: список чатів, до яких треба надіслати повідомлення
        param payer_chat_id: user_id платника
    """

    async def main() -> None:

        async with ROBOT as bot:
            sender = TelegramService(bot)
            photo_payer = (
                await sender.get_user_profile_photo(payer_user_id)
                if payer_user_id
                else None
            )
            await sender.send_message(message, chat_ids, photo_payer)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
