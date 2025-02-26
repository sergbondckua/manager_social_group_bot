import asyncio
import logging
from django.conf import settings
from celery import shared_task
from bank.models import MonoBankClient
from bank.services.mono import MonobankService, TelegramMessageSender
from common.utils import clean_tag_message
from robot.config import ROBOT

logger = logging.getLogger("monobank")


@shared_task(expires=24 * 3600)
def create_monobank_webhooks():
    """ Celery-завдання для налаштування вебхуків усіх клієнтів MonoBank. """

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

    success_count = 0
    for client in clients:
        try:
            MonobankService(client.client_token).setup_webhook(webhook_url)
            logger.info("Вебхук успішно налаштовано для клієнта %s", client.id)
            success_count += 1
        except Exception as e:
            logger.error(
                "Помилка налаштування вебхука для клієнта %s: %s",
                client.id,
                str(e),
                exc_info=True,
            )

    logger.info(
        "Налаштування завершено. Успішно: %s/%s", success_count, total_clients
    )


@shared_task
def send_telegram_message(message, chat_ids):
    """ Завдання Celery для відправки повідомлення. """
    async def main() -> None:
        async with ROBOT as bot:
            sender = TelegramMessageSender(bot)
            await sender.send_message(clean_tag_message(message), chat_ids)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())


@shared_task
def send_telegram_message_to_payer(payer_message, payer_chat_id):
    """ Завдання Celery для відправки повідомлення платникам. """
    async def main() -> None:
        async with ROBOT as bot:
            sender = TelegramMessageSender(bot)
            await sender.send_message(
                clean_tag_message(payer_message), [payer_chat_id]
            )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
