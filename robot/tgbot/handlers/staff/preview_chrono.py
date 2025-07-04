import logging
from typing import Optional, List

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from asgiref.sync import sync_to_async
from django.db.models import QuerySet
from django.utils.timezone import localtime

from chronopost.models import ScheduledMessage
from common.utils import clean_tag_message
from robot.tgbot.filters.staff import ClubStaffFilter
from robot.tgbot.keyboards import staff as kb
from robot.tgbot.text import staff as mt

logger = logging.getLogger("schedulers")

pre_post_router = Router()
pre_post_router.message.filter(ClubStaffFilter())


@sync_to_async
def get_inactive_scheduled_messages(
    limit: int = 10,
) -> QuerySet[ScheduledMessage] | None:
    """Асинхронно отримує неактивні заплановані повідомлення."""

    try:
        return ScheduledMessage.objects.filter(is_active=False).order_by(
            "-created_at"
        )[:limit]
    except Exception as e:
        logger.error("Помилка при отриманні часопостів: %s", e)
        return None


@pre_post_router.callback_query(F.data == "btn_close")
async def btn_close(callback: CallbackQuery):
    """Закриває повідомлення і видаляє клавіатуру."""
    await callback.message.delete()
    return


@pre_post_router.message(Command("chronoposts"))
async def handle_preview_chrono(message: Message):
    """Показує підготовані часопости"""

    try:
        posts = await get_inactive_scheduled_messages()
    except Exception as e:
        logger.error("Помилка при отриманні часопостів: %s", e)
        await message.bot.send_message(
            message.from_user.id,
            f"Помилка при отриманні часопостів. {e}",
        )
        return

    if await posts.acount() < 1:
        await message.bot.send_message(
            message.from_user.id,
            "😐 Немає підготовлених хронопостів або вони вже активні.",
        )
        return

    msg = []
    async for post in posts:
        msg.append(
            mt.post_template.format(
                title=post.title,
                periodicity=post.periodicity,
                scheduled_time=localtime(post.scheduled_time).strftime(
                    "%d.%m.%Y %H:%M"
                ),
                post_id=post.id,
            )
        )
    await message.bot.send_message(
        chat_id=message.from_user.id,
        text="\n".join(msg),
        reply_markup=kb.btn_close(),
    )


@pre_post_router.message(F.text.startswith("/chrono_preview_"))
async def handle_preview_chrono(message: Message):
    """Передпоказ часопосту"""

    post_id = int(message.text.split("_")[-1])
    post = await ScheduledMessage.objects.aget(id=post_id)
    keyboard = (
        kb.btn_url(post.button_text, post.button_url)
        if post.button_url and post.button_text
        else kb.btn_close()
    )
    await message.bot.send_message(
        chat_id=message.from_user.id,
        text=clean_tag_message(post.text),
        reply_markup=keyboard,
    )
