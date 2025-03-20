from aiogram import Router, F, types
from aiogram.filters import StateFilter

echo_router = Router()


@echo_router.message(F.text, StateFilter(None))
async def bot_echo(message: types.Message):
    text = ["Ехо без стану.", "Повідомлення:", message.text]
    await message.answer("\n".join(text))
