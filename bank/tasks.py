import asyncio
import logging
from django.conf import settings
from celery import shared_task
from bank.models import MonoBankClient
from bank.services.mono import MonobankService, TelegramMessageSender
from robot.config import ROBOT

logger = logging.getLogger("monobank")


@shared_task(expires=60 * 60)
def create_monobank_webhooks():
    """Celery-завдання для налаштування вебхуків усіх клієнтів MonoBank."""

    if not hasattr(settings, "BASE_URL"):
        logger.error("BASE_URL не знайдено в налаштуваннях")
        return

    webhook_path = settings.MONOBANK_WEBHOOK_PATH
    webhook_url = f"{settings.BASE_URL}{webhook_path}"

    clients = MonoBankClient.objects.all().iterator()
    total_clients = MonoBankClient.objects.count()

    if not total_clients:
        logger.info("Не знайдено клієнтів MonoBank для налаштування вебхуків")
        return

    logger.info("Початок налаштування вебхуків для %s клієнтів", total_clients)

    success_count, failure_count = 0, 0
    for client in clients:
        if MonobankService(client.client_token).setup_webhook(webhook_url):
            logger.info(
                "Вебхук успішно налаштовано для клієнта %s", client.name
            )
            success_count += 1
        else:
            logger.error(
                "Помилка налаштування вебхука для клієнта %s", client.name
            )
            failure_count += 1

    logger.info(
        "Налаштування завершено. Успішно: %s/%s, Помилки: %s",
        success_count,
        total_clients,
        failure_count,
    )


@shared_task(expires=(24 * 60 * 60) * 28)
def send_telegram_message(message, chat_ids, payer_chat_id=None):
    """Завдання Celery для відправки повідомлення."""

    async def main() -> None:
        async with ROBOT as bot:
            sender = TelegramMessageSender(bot)
            photo_payer = (
                await sender.get_user_profile_photo(payer_chat_id)
                if payer_chat_id
                else None
            )
            await sender.send_message(message, chat_ids, photo_payer)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())


@shared_task(expires=(24 * 60 * 60) * 28)
def send_telegram_message_to_payer(payer_message, payer_chat_id):
    """Завдання Celery для відправки повідомлення платникам."""

    async def main() -> None:
        async with ROBOT as bot:
            sender = TelegramMessageSender(bot)
            await sender.send_message(payer_message, [payer_chat_id])

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
