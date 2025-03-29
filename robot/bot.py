import asyncio
import os
import django
import logging

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from core.settings import ADMINS_BOT, BOT_STORAGE_URL
from robot.config import ROBOT
from robot.tgbot.handlers import routers_list
from robot.tgbot.services import broadcaster

logger = logging.getLogger("robot")


async def on_startup(bot: Bot, admin_ids: list[int]):
    await broadcaster.broadcast(bot, admin_ids, "Бот був запущений")

async def on_shutdown(bot: Bot, admin_ids: list[int]):
    pass

def get_storage():
    if BOT_STORAGE_URL:
        return RedisStorage.from_url(
            url=BOT_STORAGE_URL,
            key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True),
        )
    return MemoryStorage()


async def main():
    storage = get_storage()
    bot = ROBOT
    dp = Dispatcher(storage=storage)
    dp.include_routers(*routers_list)

    await on_startup(bot, ADMINS_BOT)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Бот був вимкнений!")
