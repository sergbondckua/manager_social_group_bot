import asyncio
import logging
from typing import List, Tuple

from asgiref.sync import sync_to_async
from django.db.models import Prefetch
from django.utils import timezone

from robot.config import ROBOT
from training_events.models import TrainingEvent, TrainingRegistration

from robot.tgbot.keyboards import member as kb
from robot.tgbot.text import member_template as mt

logger = logging.getLogger("robot")


async def process_trainings(training_ids: List[int]):
    """Асинхронна обробка тренувань"""

    # Асинхронно отримуємо тренування з пов'язаними даними
    trainings = sync_to_async(get_trainings_with_registered_participants)(
        training_ids
    )

    messages_to_send: List[Tuple[int, str, int]] = []
    seen_users = set()

    for training in await trainings:
        localized_time = timezone.localtime(training.date)

        for reg in training.registrations.all():
            user = reg.participant
            if not user.telegram_id or user.telegram_id in seen_users:
                continue

            seen_users.add(user.telegram_id)
            message_text = mt.rating_request_template.format(
                title=training.title, date=localized_time.strftime("%d.%m.%Y")
            )
            messages_to_send.append(
                (user.telegram_id, message_text, training.id)
            )

    # Відправляємо асинхронно батчами
    await send_messages_in_batches(messages_to_send)


def get_trainings_with_registered_participants(ids_list: list):
    """
    Отримує тренування з підтвердженими реєстраціями та відповідними учасниками.
    """
    if not ids_list:
        return []  # Повертаємо пустий список, якщо немає ID

    trainings = list(
        TrainingEvent.objects.filter(id__in=ids_list).prefetch_related(
            Prefetch(
                "registrations",
                queryset=TrainingRegistration.objects.select_related(
                    "participant"
                ),
            )
        )
    )
    return trainings


async def send_messages_in_batches(
    messages_list: List[Tuple[int, str, int]],
):
    """Відправляє повідомлення в батчах"""
    batch_size = 50

    for i in range(0, len(messages_list), batch_size):
        batch = messages_list[i : i + batch_size]
        async with ROBOT as bot:
            tasks = []
            for chat_id, text, training_id in batch:
                tasks.append(
                    send_single_message(bot, chat_id, text, training_id)
                )
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Обробка результатів
            for res, (chat_id, _, _) in zip(results, batch):
                if isinstance(res, Exception):
                    logger.error(
                        f"Помилка відправки для {chat_id}: {str(res)}"
                    )


async def send_single_message(bot, chat_id: int, text: str, training_id: int):
    """Відправка повідомлення"""
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=kb.rating_keyboard(training_id),
        )
        return None
    except Exception as e:
        raise e
