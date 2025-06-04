import asyncio
from datetime import timedelta

import logging
from typing import List, Tuple

from asgiref.sync import async_to_sync, sync_to_async
from celery import shared_task
from django.db.models import Prefetch
from django.utils import timezone

from robot.services.gpx_vizualizer import GPXVisualizer
from robot.tgbot.keyboards import member as kb
from robot.tgbot.text import member_template as mt
from training_events.models import TrainingEvent, TrainingRegistration

from robot.config import ROBOT

logger = logging.getLogger("robot")


@shared_task(bind=True)
def visualize_gpx(self, gpx_file: str, output_file: str = None):
    """Функція для візуалізації маршруту з GPX-файлу"""
    visualizer = GPXVisualizer(gpx_file, output_file)
    visualizer.visualize()
    return visualizer.output_file


@shared_task(bind=True)
def send_post_training_survey():
    """Функція для відправки опитування після тренування"""
    try:
        # Отримуємо всі тренування, які закінчилися протягом останніх 2 годин
        now = timezone.now()
        two_hours_ago = now - timedelta(hours=2)
        training_ids = list(
            TrainingEvent.objects.filter(
                date__gt=two_hours_ago, date__lt=now, is_cancelled=False
            ).values_list("id", flat=True)
        )

        if not training_ids:
            logger.info("Немає тренувань для опитування")
            return

            # Асинхронна обробка
        async def async_main():
            return await process_trainings(training_ids)

        async_to_sync(async_main)()
    except Exception as e:
        logger.error("Критична помилка: %s", e, exc_info=True)

async def process_trainings(training_ids: List[int]):

    # Асинхронно отримуємо тренування з пов'язаними даними
    trainings = await sync_to_async(list)(
        TrainingEvent.objects.filter(id__in=training_ids).prefetch_related(
            Prefetch(
                "registrations",
                queryset=TrainingRegistration.objects.filter(
                    is_confirmed=True
                ).select_related("participant"),
            )
        )
    )

    messages_to_send: List[Tuple[int, str]] = []
    seen_users = set()

    for training in trainings:
        localized_time = timezone.localtime(training.date)

        for reg in training.registrations.all():
            user = reg.participant
            if not user.telegram_id or user.telegram_id in seen_users:
                continue

            seen_users.add(user.telegram_id)
            message_text = mt.rating_request_template.format(
                title=training.title,
                date=localized_time.strftime("%d.%m.%Y")
            )
            messages_to_send.append((
                user.telegram_id,
                message_text
            ))

    # Відправляємо асинхронно батчами
    await send_messages_in_batches(messages_to_send)

async def send_messages_in_batches(messages: List[Tuple[int, str]]):
    batch_size = 50

    for i in range(0, len(messages), batch_size):
        batch = messages[i:i+batch_size]
        async with ROBOT as bot:
            tasks = []
            for chat_id, text in batch:
                tasks.append(
                    send_single_message(bot, chat_id, text)
                )
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Обробка результатів
            for res, (chat_id, _) in zip(results, batch):
                if isinstance(res, Exception):
                    logger.error(f"Помилка відправки для {chat_id}: {str(res)}")

async def send_single_message(bot, chat_id: int, text: str):
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=kb.rating_and_comment_keyboard
        )
        return None
    except Exception as e:
        # Додаткова обробка специфічних помилок
        if "bot was blocked" in str(e).lower():
            return None  # Спеціальна обробка
        raise e
