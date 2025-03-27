from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from robot.tgbot.text.user_template import msg_my_id

user_router = Router()


@user_router.message(CommandStart())
async def admin_start(message: Message):
    await message.reply(
        f"Вітаю, {message.from_user.mention_html(message.from_user.first_name)}!"
    )


@user_router.message(Command(commands=["myid", "my_id"]))
async def handle_my_id(message: Message):
    await message.answer(
        msg_my_id.format(
            user_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username or "",
            chat_id=message.chat.id,
            title=message.chat.title or message.from_user.full_name,
        )
    )
