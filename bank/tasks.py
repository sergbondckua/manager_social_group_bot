import logging
from django.conf import settings
from celery import shared_task
from bank.models import MonoBankClient
from bank.services.mono import MonobankService

logger = logging.getLogger("monobank")


@shared_task(expires=24 * 3600)
def create_monobank_webhooks():
    """
    Celery-завдання для налаштування вебхуків усіх клієнтів MonoBank.
    Обробляє помилки для кожного клієнта окремо та логує результат.
    """
    webhook_path = getattr(
        settings, "MONOBANK_WEBHOOK_PATH", "/bank/webhook/monobank/"
    )
    webhook_url = (
        f"{settings.BASE_URL}{webhook_path}"
        if hasattr(settings, "BASE_URL")
        else webhook_path
    )

    clients = MonoBankClient.objects.all()
    total_clients = clients.count()

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
        f"Налаштування завершено. Успішно: {success_count}/{total_clients}"
    )
