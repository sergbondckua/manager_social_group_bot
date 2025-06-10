import asyncio
import os
from datetime import timedelta

import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from robot.services.gpx_vizualizer import GPXVisualizer
from robot.tgbot.services.training_survey_service import process_trainings
from training_events.models import TrainingEvent, TrainingDistance

logger = logging.getLogger("robot")


@shared_task(bind=True)
def visualize_gpx(self, gpx_file: str, output_file: str = None):
    """Функція для візуалізації маршруту з GPX-файлу"""
    visualizer = GPXVisualizer(gpx_file, output_file)
    visualizer.visualize()
    return visualizer.output_file


def visualize_gpx_web(gpx_file: str, output_file: str = None):
    """Функція для візуалізації маршруту з GPX-файлу"""
    visualizer = GPXVisualizer(gpx_file, output_file)
    visualizer.visualize()
    return visualizer.output_file


@shared_task(bind=True, max_retries=3)
def create_route_visualization_task(self, distance_id):
    """
    Асинхронна задача для створення візуалізації маршруту

    Args:
        distance_id: ID об'єкта TrainingDistance
    """
    try:
        # Імпортуємо модель всередині задачі для уникнення циклічних імпортів

        # Отримуємо об'єкт дистанції
        try:
            distance = TrainingDistance.objects.get(pk=distance_id)
        except TrainingDistance.DoesNotExist:
            logger.error("TrainingDistance з ID %s не знайдено", distance_id)
            return False

        # Перевіряємо чи є GPX файл
        if not distance.route_gpx:
            logger.warning("GPX файл відсутній для дистанції ID %s", distance_id)
            TrainingDistance.objects.filter(pk=distance_id).update(
                map_processing_status="failed"
            )
            return False

        # Оновлюємо статус на "обробляється"
        TrainingDistance.objects.filter(pk=distance_id).update(
            map_processing_status="processing"
        )

        # Отримуємо шлях до GPX файлу
        gpx_path = distance.route_gpx.path

        # Перевіряємо чи існує GPX файл
        if not os.path.exists(gpx_path):
            logger.error("GPX файл не існує: %s", gpx_path)
            TrainingDistance.objects.filter(pk=distance_id).update(
                map_processing_status="failed"
            )
            return False

        # Створюємо шлях для PNG файлу
        png_path = os.path.splitext(gpx_path)[0] + ".png"

        # Створюємо директорію якщо не існує
        png_dir = os.path.dirname(png_path)
        os.makedirs(png_dir, exist_ok=True)

        # Створюємо візуалізацію
        visualization_success = visualize_gpx_web(gpx_path, png_path)

        if visualization_success and os.path.exists(png_path):
            # Отримуємо відносний шлях для збереження в базі даних
            relative_path = os.path.relpath(png_path, settings.MEDIA_ROOT)

            # Оновлюємо об'єкт з новою картою та статусом
            TrainingDistance.objects.filter(pk=distance_id).update(
                route_gpx_map=relative_path, map_processing_status="completed"
            )

            logger.info(
                "Візуалізація успішно створена для дистанції ID %s: %s",
                distance_id,
                relative_path,
            )
            return True
        else:
            logger.error(
                "Не вдалося створити візуалізацію для дистанції %s", distance_id
            )
            TrainingDistance.objects.filter(pk=distance_id).update(
                map_processing_status="failed"
            )
            return False

    except Exception as exc:
        logger.error(
            "Помилка при створенні візуалізації для дистанції %s: %s",
            distance_id,
            exc,
        )

        # Оновлюємо статус на помилку
        try:
            TrainingDistance.objects.filter(pk=distance_id).update(
                map_processing_status="failed"
            )
        except Exception:
            pass

        # Повторюємо задачу до 3 разів з експоненційною затримкою
        if self.request.retries < self.max_retries:
            logger.info(
                "Повторюємо задачу для дистанції %s (спроба %d)",
                distance_id,
                self.request.retries + 1,
            )
            raise self.retry(countdown=60 * (2**self.request.retries))

        return False


@shared_task
def send_post_training_survey():
    """Функція для відправки опитування після тренування"""
    try:
        # Отримуємо всі тренування, які закінчилися протягом останніх 2 годин
        now = timezone.localtime(timezone.now())
        two_hours_ago = now - timedelta(hours=2)
        training_ids = list(
            TrainingEvent.objects.filter(
                date__lte=two_hours_ago,  # Тренування почалося до або рівно 2 години тому
                is_feedback_sent=False,  # Запит на оцінювання ще не відправлений
                is_cancelled=False,
            ).values_list("id", flat=True)
        )

        if not training_ids:
            logger.info("Немає тренувань для опитування")
            return

        async def main():
            await process_trainings(training_ids)
            # Помічаємо ці тренування як "запит на оцінювання відправлено"
            await TrainingEvent.objects.filter(id__in=training_ids).aupdate(
                is_feedback_sent=True
            )

        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())

    except Exception as e:
        logger.error("Критична помилка: %s", e, exc_info=True)
