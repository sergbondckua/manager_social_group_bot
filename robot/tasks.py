import asyncio
from datetime import timedelta

import logging

from celery import shared_task
from django.utils import timezone

from robot.services.gpx_vizualizer import GPXVisualizer
from robot.tgbot.services.training_survey_service import process_trainings
from training_events.models import TrainingEvent

logger = logging.getLogger("robot")


@shared_task(bind=True)
def visualize_gpx(gpx_file: str, output_file: str = None, *args, **kwargs):
    """Функція для візуалізації маршруту з GPX-файлу"""
    visualizer = GPXVisualizer(gpx_file, output_file)
    visualizer.visualize()
    return visualizer.output_file


@shared_task(bind=True)
def send_post_training_survey(*args, **kwargs):
    """Функція для відправки опитування після тренування"""
    try:
        # Отримуємо всі тренування, які закінчилися протягом останніх 2 годин
        now = timezone.localtime(timezone.now())
        two_hours_ago = now - timedelta(hours=2)
        training_ids = list(
            TrainingEvent.objects.filter(
                date__gt=two_hours_ago, date__lt=now, is_cancelled=False
            ).values_list("id", flat=True)
        )

        if not training_ids:
            logger.info("Немає тренувань для опитування")
            return

        async def main():
            return await process_trainings(training_ids)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())

    except Exception as e:
        logger.error("Критична помилка: %s", e, exc_info=True)
