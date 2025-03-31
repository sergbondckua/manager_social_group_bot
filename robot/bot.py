import logging
import asyncio
import os
from typing import Union, NoReturn

import django

from robot.tgbot.services import broadcaster

# Ініціалізація Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage


from core.settings import BOT_STORAGE_URL, ADMINS_BOT
from robot.config import ROBOT
from robot.tgbot.handlers import routers_list

# Логування
logger = logging.getLogger("robot")


def get_storage() -> Union[RedisStorage, MemoryStorage]:
    """Ініціалізує сховище для бота залежно від наявності Redis."""
    if BOT_STORAGE_URL:
        return RedisStorage.from_url(
            url=BOT_STORAGE_URL,
            key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True),
        )
    return MemoryStorage()


async def on_startup(bot: Bot, admin_ids: list[int]) -> NoReturn:
    """Повідомляє адміністраторів про запуск бота."""
    try:
        await broadcaster.broadcast(bot, admin_ids, "Бот був запущений")
        logger.info("Повідомлення адміністраторам успішно відправлено.")
    except Exception as e:
        logger.error(
            "Помилка при надсиланні повідомлення адміністраторам: %s", e
        )


async def main():
    """Головна функція для запуску бота."""

    # Ініціалізація бота та диспетчера
    dp = Dispatcher(storage=get_storage())
    dp.include_routers(*routers_list)

    await dp.start_polling(ROBOT)
    await on_startup(ROBOT, ADMINS_BOT)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Бот був вимкнений!")
