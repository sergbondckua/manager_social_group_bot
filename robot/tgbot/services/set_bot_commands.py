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
                types.BotCommand(command="myid", description="Ваші ID дані"),
            ],
            scope=types.BotCommandScopeDefault(),
            language_code="uk",
        )
    )
