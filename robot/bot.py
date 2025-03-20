import asyncio
import os
import django
import logging

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from core.settings import ADMINS_BOT
from robot.config import ROBOT
from robot.tgbot.handlers import routers_list
from robot.tgbot.services import broadcaster

logger = logging.getLogger("robot")


async def on_startup(bot: Bot, admin_ids: list[int]):
    await broadcaster.broadcast(bot, admin_ids, "Бот був запущений")


async def main():

    storage = MemoryStorage()
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
