import logging

from aiogram import types, Bot
from aiogram.methods import SetMyCommands

logger = logging.getLogger("robot")


async def set_default_commands(bot: Bot):
    """Встановлює звичайні команди для бота."""
    logger.info("Встановлення звичайних команд для бота")

    return await bot(
        SetMyCommands(
            commands=[
                types.BotCommand(
                    command="start", description="Актувуйте бота"
                ),
                types.BotCommand(command="help", description="Довідка"),
                types.BotCommand(command="my_id", description="Ваші ID дані"),
                types.BotCommand(
                    command="weather_now", description="Поточна погода"
                ),
                types.BotCommand(
                    command="my_trainings", description="Мої тренування"
                ),
                types.BotCommand(
                    command="create_training",
                    description="Створити тренування (тільки для адмінів)",
                ),
                types.BotCommand(
                    command="trainings", description="Створені тренування (тільки для адмінів)"
                ),
            ],
            scope=types.BotCommandScopeDefault(),
            language_code="uk",
        )
    )
