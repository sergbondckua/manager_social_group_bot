import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from aiogram import Bot, types
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaDocument
from asgiref.sync import sync_to_async
from celery.result import AsyncResult
from django.conf import settings

from robot.tasks import visualize_gpx
from training_events.models import TrainingDistance, TrainingEvent
from robot.tgbot.text import staff_create_training as mt
from robot.tgbot.keyboards import staff as kb

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
            task = visualize_gpx.delay(
                gpx_file=str(route_path), output_file=map_image_path
            )
            # Очікуємо завершення задачи
            await wait_for_task_completion(task.task_id)
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
        updates["route_gpx"] = route_path.replace(
            str(settings.MEDIA_ROOT), ""
        ).lstrip("/")

    if map_image_path:
        updates["route_gpx_map"] = map_image_path.replace(
            str(settings.MEDIA_ROOT), ""
        ).lstrip("/")

    if updates:
        await sync_to_async(
            lambda: [
                setattr(distance_obj, key, value)
                for key, value in updates.items()
            ]
        )()
        await sync_to_async(distance_obj.save)()


async def wait_for_task_completion(task_id: str, max_wait_time: int = 60):
    """Очікування завершення задачі Celery.

    Args:
        task_id (str): Ідентифікатор задачі.
        max_wait_time (int, optional): Максимальний час очікування (в секундах).
    """

    wait_interval = 2  # перевіряємо кожні 2 секунди
    total_waited = 0

    while total_waited < max_wait_time:
        # Отримуємо результат задачі
        task_result = AsyncResult(task_id)

        # Перевіряємо статус
        if task_result.ready():
            if task_result.successful():
                return
            else:
                # Отримуємо деталі помилки
                error = task_result.result
                raise Exception("Помилка задачі: %s", str(error))

        # Почекаємо перед наступною перевіркою
        await asyncio.sleep(wait_interval)
        total_waited += wait_interval

    # Якщо час вийшов
    raise TimeoutError(
        f"Фонова задача не завершилася за {max_wait_time} секунд"
    )


async def wait_for_file_exist(file_path: Path, max_wait_time: int = 60):
    """Очікуємо появу файлу"""
    wait_interval = 2  # перевіряємо кожні 2 секунди
    total_waited = 0

    while total_waited < max_wait_time:
        if file_path.exists():
            return

        # Почекаємо перед наступною перевіркою
        await asyncio.sleep(wait_interval)
        total_waited += wait_interval

    raise TimeoutError(f"Файли не з'явилися за {max_wait_time} секунд")


async def publish_training_message(
    training: TrainingEvent, distances: list, callback: types.CallbackQuery
):
    """Відправляє основне повідомлення про тренування."""
    message_text = await mt.format_success_message(training, distances)
    keyboard = kb.register_training_keyboard(training.id)

    if training.poster:
        await callback.message.bot.send_chat_action(
            callback.message.chat.id, action="upload_photo"
        )
        photo_file = FSInputFile(training.poster.path)
        await callback.message.bot.send_photo(
            chat_id=settings.DEFAULT_CHAT_ID,
            photo=photo_file,
            caption=message_text,
            reply_markup=keyboard,
        )
    else:
        await callback.message.bot.send_chat_action(
            callback.message.chat.id, action="typing"
        )
        await callback.message.bot.send_message(
            chat_id=settings.DEFAULT_CHAT_ID,
            text=message_text,
            reply_markup=keyboard,
        )


async def prepare_media_groups(
    training: TrainingEvent, distances: list
) -> tuple[list, list]:
    """Готує медіагрупи для GPX та PNG файлів."""
    gpx_group = []
    img_group = []

    for num, distance in enumerate(distances):
        if not distance.route_gpx:
            continue

        gpx_group.append(create_gpx_media(distance, training.id))

        try:
            png_path = Path(distance.route_gpx_map.path)
            await wait_for_file_exist(png_path)
            img_group.append(create_png_media(png_path, training, num))
        except TimeoutError:
            logger.warning("PNG не знайдено: %s", png_path)

    return gpx_group, img_group


def create_gpx_media(distance, training_id):
    """Створює об'єкт медіа для GPX файлу."""
    return InputMediaDocument(
        media=FSInputFile(distance.route_gpx.path),
        caption=f"Маршрут {distance.distance} км\n"
               f"#{training_id}тренування #{int(distance.distance)}км",
    )

def create_png_media(png_path, training, num):
    """Створює об'єкт медіа для PNG файлу."""
    return InputMediaPhoto(
        media=FSInputFile(png_path),
        caption=(
            f"Візуалізація маршруту(ів) {training.title}\n"
            f"#{training.id}тренування" if num == 0 else None
        ),
    )


def any_has_gpx(distances: list) -> bool:
    """Перевіряє, чи є серед дистанцій GPX файли."""
    return any(distance.route_gpx for distance in distances)


async def handle_gpx_files(
    training: TrainingEvent, distances: list, callback: types.CallbackQuery
):
    """Обробляє та відправляє GPX файли та візуалізації."""
    find_png_msg = await notify_about_visualization_search(callback)
    gpx_group, img_group = await prepare_media_groups(training, distances)
    await send_media_groups(gpx_group, img_group, callback)
    await cleanup_search_message(find_png_msg)


async def notify_about_visualization_search(
    callback: types.CallbackQuery,
) -> types.Message:
    """Відправляє повідомлення про пошук візуалізацій."""
    return await callback.message.bot.send_message(
        chat_id=settings.DEFAULT_CHAT_ID,
        text="🔍 Пошук візуалізації маршрутів...",
    )


async def send_media_groups(gpx_group, img_group, callback):
    """Відправляє медіагрупи в чат."""
    if gpx_group:
        await callback.message.bot.send_chat_action(
            settings.DEFAULT_CHAT_ID, action="upload_document"
        )
        await callback.message.bot.send_media_group(
            chat_id=settings.DEFAULT_CHAT_ID,
            media=gpx_group,
        )
    if img_group:
        await callback.message.bot.send_chat_action(
            settings.DEFAULT_CHAT_ID, action="upload_photo"
        )
        await callback.message.bot.send_media_group(
            chat_id=settings.DEFAULT_CHAT_ID,
            media=img_group,
        )

async def cleanup_search_message(message: types.Message):
    """Видаляє проміжне повідомлення про пошук."""
    if message:
        try:
            await message.delete()
        except Exception as e:
            logger.error("Помилка видалення повідомлення: %s", e)

async def confirm_publication(training: TrainingEvent, callback: types.CallbackQuery):
    """Підтверджує успішну публікацію."""
    await callback.message.bot.send_chat_action(
        callback.message.chat.id, action="typing"
    )
    await callback.message.edit_text(
        text=f"♻️ Тренування {training.title} опубліковано!",
        reply_markup=None,
    )