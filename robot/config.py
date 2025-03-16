from dataclasses import dataclass

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from environs import Env

from core.settings import TELEGRAM_BOT_TOKEN

# Створіть об'єкт ENV.
# Об'єкт ENV буде використовуватися для читання змінних середовища.
env = Env()
env.read_env()


@dataclass
class TgBot:
    """Створює об'єкт TGBOT із змінних середовищ."""

    token: str
    admin_ids: list[int]

    @staticmethod
    def from_env(environment: Env) -> "TgBot":
        """
        Створює об'єкт TGBOT із змінних середовищ.
        """
        token = environment.str("TELEGRAM_BOT_TOKEN")
        admin_ids = environment.list("ADMINS_BOT")
        return TgBot(token=token, admin_ids=admin_ids)


config_bot = TgBot.from_env(env)

ROBOT = Bot(
    token=TELEGRAM_BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
