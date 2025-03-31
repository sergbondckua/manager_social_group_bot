import asyncio
import logging
from typing import Union

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

from core.settings import ADMINS_BOT, BOT_STORAGE_URL, TELEGRAM_WEBHOOK_URL
from robot.config import ROBOT
from robot.tgbot.handlers import routers_list
from robot.tgbot.services import broadcaster

logger = logging.getLogger("robot")


def get_storage() -> Union[RedisStorage, MemoryStorage]:
    """Ініціалізує сховище для бота залежно від наявності Redis."""
    if BOT_STORAGE_URL:
        return RedisStorage.from_url(
            url=BOT_STORAGE_URL,
            key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True),
        )
    return MemoryStorage()


async def on_startup(bot: Bot, admin_ids: list[int]):
    """Повідомляє адміністраторів про запуск бота."""
    try:
        await broadcaster.broadcast(bot, admin_ids, "Бот був запущений")
        logger.info("Повідомлення адміністраторам успішно відправлено.")
    except Exception as e:
        logger.error(
            "Помилка при надсиланні повідомлення адміністраторам: %s", e
        )


async def set_webhook():
    """Встановлює webhook для бота."""
    try:
        await bot.delete_webhook()
        await bot.set_webhook(TELEGRAM_WEBHOOK_URL)
        logger.info("Webhook встановлено на URL: %s", TELEGRAM_WEBHOOK_URL)
    except Exception as e:
        logger.error("Не вдалося встановити webhook: %s", e)


def setup_webhook():
    """Синхронно налаштовує webhook для бота."""
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(set_webhook())
    except Exception as e:
        logger.error("Не вдалося встановити webhook: %s", e)


async def feed_update(update_data: dict):
    """Передає оновлення диспетчеру бота."""
    try:
        await dp.feed_webhook_update(bot=bot, update=update_data)
    except Exception as e:
        logger.error("Помилка при обробці оновлення: %s", e)


def process_update(update_data: dict):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(feed_update(update_data))
        loop.close()
    except Exception as e:
        logger.error("Помилка при обробці оновлення: %s", e)


# Ініціалізація диспетчера та бота
storage = get_storage()
bot = ROBOT
dp = Dispatcher(storage=storage)
dp.include_routers(*routers_list)
