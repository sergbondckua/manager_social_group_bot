import asyncio
import logging

from django.core.management.base import BaseCommand

from robot.bot import main

# Логування
logger = logging.getLogger("robot")


class Command(BaseCommand):
    help = "Запускає Telegram-бота"

    def handle(self, *args, **kwargs):
        try:
            asyncio.run(main())
        except (KeyboardInterrupt, SystemExit):
            logger.error("Бот був вимкнений!")