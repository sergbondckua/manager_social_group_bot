import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from aiogram import Bot
from asgiref.sync import sync_to_async
from django.conf import settings

from robot.tasks import visualize_gpx
from training_events.models import TrainingDistance


logger = logging.getLogger("robot")

async def download_file_safe(bot, file_id: str, destination: str) -> bool:
    """Безпечно завантажує файл."""
    try:
        file = await bot.get_file(file_id)
        await bot.download_file(
            file_path=file.file_path, destination=destination
        )
        return True
    except Exception as e:
        logger.error(f"Помилка завантаження файлу {file_id}: {e}")
        return False


async def create_poster_path(
    club_user_id: int, file_id: str, bot
) -> Optional[str]:
    """Створює шлях для постера та завантажує його."""
    try:
        file = await bot.get_file(file_id)
        file_name = file.file_path.split("/")[-1]
        save_path = (
            Path(settings.MEDIA_ROOT) / f"trainings/{club_user_id}/images"
        )
        save_path.mkdir(parents=True, exist_ok=True)

        poster_path = save_path / file_name

        if await download_file_safe(bot, file_id, str(poster_path)):
            return str(poster_path)
        return None
    except Exception as e:
        logger.error(f"Помилка створення шляху постера: {e}")
        return None


async def create_route_path(
    club_user_id: int,
    distance: float,
    training_date: datetime,
    file_id: str,
    bot: Bot,
) -> tuple[Optional[str], Optional[str]]:
    """Створює шлях для маршруту та завантажує його."""
    try:
        file = await bot.get_file(file_id)
        file_extension = file.file_path.split("/")[-1].split(".")[-1]
        file_name = f"{distance}km_{training_date.strftime('%d%B%Y_%H%M')}.{file_extension}"

        save_path = Path(settings.MEDIA_ROOT) / f"trainings/{club_user_id}/gpx"
        save_path.mkdir(parents=True, exist_ok=True)

        route_path = save_path / file_name

        if await download_file_safe(bot, file_id, str(route_path)):
            map_image_path = str(route_path).replace(".gpx", ".png")
            # Запускаємо Celery-задачу асинхронно
            visualize_gpx.delay(
                gpx_file=str(route_path), output_file=map_image_path
            )
            return str(route_path), map_image_path
        return None, None
    except Exception as e:
        logger.error(f"Помилка створення шляху маршруту: {e}")
        return None, None


async def process_gpx_files_after_creation(
    created_distances_info: list[dict],
    club_user_id: int,
    training_datetime: datetime,
    bot: Bot,
) -> list[TrainingDistance]:
    """
    Обробляє GPX файли після створення записів у БД

    Args:
        created_distances_info: Список словників з інформацією про дистанції
        club_user_id: ID користувача клубу
        training_datetime: Дата та час тренування
        bot: Екземпляр Telegram бота

    Returns:
        Список об'єктів TrainingDistance з оновленими шляхами до файлів
    """
    created_distances = []

    for info in created_distances_info:
        distance_obj = info["distance_obj"]
        distance_data = info["distance_data"]

        # Пропускаємо дистанції без GPX файлу
        if not distance_data.get("route_gpx"):
            created_distances.append(distance_obj)
            continue

        # Створюємо шляхи для GPX файлу та мапи
        route_path, map_image_path = await create_route_path(
            club_user_id,
            distance_data["distance"],
            training_datetime,
            distance_data["route_gpx"],
            bot,
        )

        # Оновлюємо шляхи в базі даних
        if route_path or map_image_path:
            await update_distance_paths(
                distance_obj, route_path, map_image_path
            )

        created_distances.append(distance_obj)

    return created_distances


async def update_distance_paths(
    distance_obj: TrainingDistance,
    route_path: Optional[str],
    map_image_path: Optional[str],
) -> None:
    """
    Оновлює шляхи до файлів маршруту в об'єкті дистанції

    Args:
        distance_obj: Об'єкт дистанції тренування
        route_path: Шлях до файлу GPX
        map_image_path: Шлях до зображення мапи
    """
    updates = {}

    if route_path:
        updates["route_gpx"] = route_path.replace(str(settings.MEDIA_ROOT), "")

    if map_image_path:
        updates["route_gpx_map"] = map_image_path.replace(
            str(settings.MEDIA_ROOT), ""
        )

    if updates:
        await sync_to_async(
            lambda: [
                setattr(distance_obj, key, value)
                for key, value in updates.items()
            ]
        )()
        await sync_to_async(distance_obj.save)()
