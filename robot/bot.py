import asyncio
import logging
import nest_asyncio
from typing import Union

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

from core.settings import ADMINS_BOT, BOT_STORAGE_URL, TELEGRAM_WEBHOOK_URL
from robot.config import ROBOT
from robot.tgbot.handlers import routers_list
from robot.tgbot.services import broadcaster

# Застосовуємо nest_asyncio для роботи asyncio всередині Django
nest_asyncio.apply()

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
    asyncio.run(set_webhook())


# Створюємо або отримуємо існуючий цикл подій
def get_event_loop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        # Якщо циклу подій немає в поточному потоці
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


# Функція для обробки оновлень від Telegram
def process_update(update_data):
    """Обробляє оновлення від Telegram"""
    loop = get_event_loop()
    # Запускаємо обробку оновлення в існуючому циклі подій
    if loop.is_running():
        # Якщо цикл подій вже запущено, додаємо як завдання
        asyncio.create_task(feed_update(update_data))
    else:
        # Інакше запускаємо нове виконання
        loop.run_until_complete(feed_update(update_data))


async def feed_update(update_data):
    """Асинхронно передає оновлення диспетчеру бота"""
    try:
        # В aiogram 3.x потрібно використовувати feed_webhook_update
        await dp.feed_webhook_update(bot=bot, update=update_data)
    except Exception as e:
        logger.error(f"Помилка при обробці оновлення: {e}")
        import traceback

        logger.error(traceback.format_exc())


# Ініціалізація диспетчера та бота
storage = get_storage()
bot = ROBOT
dp = Dispatcher(storage=storage)
dp.include_routers(*routers_list)
