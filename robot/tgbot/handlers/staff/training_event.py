import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from aiogram import types, Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction

from profiles.models import ClubUser
from robot.tasks import visualize_gpx
from robot.tgbot.filters.staff import ClubStaffFilter
from robot.tgbot.keyboards import staff as kb
from robot.tgbot.misc import validators
from robot.tgbot.services.staff_training_service import (
    create_poster_path,
    process_gpx_files_after_creation,
)
from robot.tgbot.states.staff import CreateTraining
from robot.tgbot.text import staff_create_training as mt
from training_events.models import TrainingEvent, TrainingDistance

# Налаштування логування
logger = logging.getLogger("robot")

staff_router = Router()
staff_router.message.filter(ClubStaffFilter())

SKIP_AND_CANCEL_BUTTONS = kb.skip_and_cancel_keyboard()
CANCEL_BUTTON = kb.cancel_keyboard()


async def get_club_user(telegram_id: int) -> Optional[ClubUser]:
    """Отримує користувача клубу за Telegram ID."""
    try:
        return await ClubUser.objects.aget(telegram_id=telegram_id)
    except ClubUser.DoesNotExist:
        return None


def parse_date(date_str: str) -> Optional[datetime]:
    """Парсить дату з рядка."""
    try:
        normalized_date = (
            date_str.strip()
            .replace("/", ".")
            .replace(",", ".")
            .replace(" ", ".")
        )
        return datetime.strptime(normalized_date, "%d.%m.%Y")
    except ValueError:
        return None


def parse_time(time_str: str) -> Optional[datetime]:
    """Парсить час з рядка."""
    try:
        normalized_time = (
            time_str.strip()
            .replace("/", ":")
            .replace(",", ":")
            .replace(" ", ":")
            .replace(".", ":")
        )
        return datetime.strptime(normalized_time, "%H:%M")
    except ValueError:
        return None


def parse_pace(pace_str: str) -> str:
    """Парсить та нормалізує темп."""
    return (
        pace_str.strip().replace(".", ":").replace(",", ":").replace(" ", ":")
    )


async def clear_state_and_notify(
    message: types.Message,
    state: FSMContext,
    text: str,
    prev_delete_message: bool = False,
):
    """Очищує стан та надсилає повідомлення."""
    await state.clear()
    # Видалення попереднього повідомлення
    if prev_delete_message:
        await message.delete()
    await message.answer(text, reply_markup=types.ReplyKeyboardRemove())


@staff_router.message(F.text == mt.btn_cancel)
async def cancel_training_creation(message: types.Message, state: FSMContext):
    """Скасування створення тренування."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Немає активного процесу, який можна скасувати.")
        return

    await clear_state_and_notify(
        message, state, "❌ Створення тренування скасовано."
    )


# Обробник команди для перегляду створених тренувань
@staff_router.message(Command("my_trainings"))
async def cmd_my_trainings(message: types.Message):
    """Показує список тренувань, створених користувачем."""
    user_id = message.from_user.id
    club_user = await get_club_user(message.from_user.id)
    if not club_user:
        await message.bot.send_message(
            user_id,
            "❌ Ваш обліковий запис не знайдено в системі. Зверніться до адміністратора.",
        )
        return

    # Отримуємо тренування користувача
    @sync_to_async
    def get_trainings(user):
        return list(
            TrainingEvent.objects.filter(created_by=user).order_by("-date")[
                :10
            ]
        )

    trainings = await get_trainings(club_user)

    if not trainings:
        await message.bot.send_message(
            user_id, "📝 Ви ще не створювали тренувань."
        )
        return

    message_parts = ["📋 Ваші останні тренування:", ""]

    for training in trainings:
        status = "🔜" if training.date > timezone.now() else "✅"
        message_parts.append(
            f"{status} {training.title}\n"
            f"📅 {training.date.strftime('%d.%m.%Y %H:%M')}\n"
            f"📍 {training.location}\n"
            f"🆔 ID: {training.id}\n"
            "\n ================\n\n"
        )
    await message.bot.send_message(user_id, "\n".join(message_parts))


@staff_router.message(Command("create_training"))
async def cmd_create_training(message: types.Message, state: FSMContext):
    """Обробник команди "/create_training"."""

    # Перевіряємо, чи користувач має права
    club_user = await get_club_user(message.from_user.id)
    if not club_user:
        await message.answer(
            "❌ Ваш обліковий запис не знайдено в системі. "
            "Зверніться до адміністратора."
        )
        return

    await state.set_state(CreateTraining.waiting_for_title)
    await message.bot.send_message(
        chat_id=message.from_user.id,
        text="Введіть назву тренування:",
        reply_markup=CANCEL_BUTTON,
    )


@staff_router.message(CreateTraining.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    """Обробник введення назви тренування."""
    title = message.text.strip()

    if not validators.validate_title(title):
        await message.answer(
            "Назва тренування не відповідає вимогам "
            f"({validators.MIN_TITLE_LENGTH}-{validators.MAX_TITLE_LENGTH} символів). "
            "Спробуйте ще раз:"
        )
        return

    # Перевіряємо унікальність назви
    if await TrainingEvent.objects.filter(title=title).aexists():
        await message.answer(
            f"❌ Тренування з назвою '{title}' вже існує. "
            "Оберіть іншу назву:"
        )
        return

    await state.update_data(title=title)
    await state.set_state(CreateTraining.waiting_for_description)
    await message.answer(
        "Введіть опис тренування (або /skip для пропуску):",
        reply_markup=SKIP_AND_CANCEL_BUTTONS,
    )


@staff_router.message(
    CreateTraining.waiting_for_description,
    lambda message: message.text in {"/skip", mt.btn_skip},
)
async def skip_description(message: types.Message, state: FSMContext):
    """Пропуск опису тренування."""
    await state.update_data(description="")
    await state.set_state(CreateTraining.waiting_for_date)
    await message.answer(
        "Введіть дату тренування у форматі ДД.ММ.РРРР:",
        reply_markup=CANCEL_BUTTON,
    )


@staff_router.message(CreateTraining.waiting_for_description)
async def process_training_description(
    message: types.Message, state: FSMContext
):
    """Обробник введення опису тренування."""
    await state.update_data(description=message.text.strip())
    await state.set_state(CreateTraining.waiting_for_date)
    await message.answer(
        "Введіть дату тренування у форматі ДД.ММ.РРРР:",
        reply_markup=CANCEL_BUTTON,
    )


@staff_router.message(CreateTraining.waiting_for_date)
async def process_training_date(message: types.Message, state: FSMContext):
    """Обробник введення дати тренування."""
    parsed_date = parse_date(message.text.lstrip().rstrip())

    if not parsed_date:
        await message.answer(
            "Некоректний формат дати. "
            "Введіть дату у форматі ДД.ММ.РРРР (наприклад, 25.12.2025):"
        )
        return

    # Перевіряємо, що дата не в минулому
    if parsed_date.date() < timezone.now().date():
        await message.answer(
            "Дата тренування не може бути в минулому. Введіть коректну дату:"
        )
        return

    await state.update_data(date=parsed_date.strftime("%d.%m.%Y"))
    await state.set_state(CreateTraining.waiting_for_time)
    await message.answer("Введіть час тренування у форматі ГГ:ММ:")


@staff_router.message(CreateTraining.waiting_for_time)
async def process_training_time(message: types.Message, state: FSMContext):
    """Обробник введення часу тренування."""
    parsed_time = parse_time(message.text.lstrip().rstrip())

    if not parsed_time:
        await message.answer(
            "Некоректний формат часу. "
            "Введіть час у форматі ГГ:ММ (наприклад, 08:30):"
        )
        return

    # Додаткова перевірка на коректність часу для сьогоднішньої дати
    data = await state.get_data()
    training_date = datetime.strptime(data["date"], "%d.%m.%Y").date()
    training_datetime = datetime.combine(training_date, parsed_time.time())

    if training_datetime < datetime.now():
        await message.answer(
            "Час тренування не може бути в минулому. Введіть коректний час:"
        )
        return

    await state.update_data(time=parsed_time.strftime("%H:%M"))
    await state.set_state(CreateTraining.waiting_for_location)
    await message.answer("Введіть місце зустрічі для тренування:")


@staff_router.message(CreateTraining.waiting_for_location)
async def process_training_location(message: types.Message, state: FSMContext):
    """Обробник введення місця тренування."""
    location = message.text.strip()

    if not validators.validate_location(location):
        await message.answer(
            "Місце зустрічі не відповідає вимогам "
            f"({validators.MIN_LOCATION_LENGTH}-{validators.MAX_LOCATION_LENGTH} символів). "
            "Спробуйте ще раз:"
        )
        return

    await state.update_data(location=location)
    await state.set_state(CreateTraining.waiting_for_poster)
    await message.answer(
        "Завантажте постер тренування (фото) або /skip:",
        reply_markup=SKIP_AND_CANCEL_BUTTONS,
    )


@staff_router.message(
    CreateTraining.waiting_for_poster,
    lambda message: message.text in {"/skip", mt.btn_skip},
)
async def skip_poster(message: types.Message, state: FSMContext):
    """Пропуск додавання постеру тренування."""
    await state.update_data(poster_file_id=None, distances=[])
    await state.set_state(CreateTraining.waiting_for_distance)
    await message.answer(
        "Тепер додамо дистанції для тренування.\n"
        "Введіть першу дистанцію (у кілометрах):",
        reply_markup=CANCEL_BUTTON,
    )


@staff_router.message(CreateTraining.waiting_for_poster, F.photo)
async def process_training_poster(message: types.Message, state: FSMContext):
    """Обробник введення постеру тренування."""
    try:
        file_id = message.photo[-1].file_id
        await state.update_data(poster_file_id=file_id, distances=[])
        await state.set_state(CreateTraining.waiting_for_distance)
        await message.answer(
            "Введіть першу дистанцію (у кілометрах):",
            reply_markup=CANCEL_BUTTON,
        )
    except Exception as e:
        logger.error(f"Помилка завантаження постера: {e}")
        await message.answer("Неможливо завантажити постер. Спробуйте ще раз:")


@staff_router.message(CreateTraining.waiting_for_poster)
async def process_invalid_poster_message(message: types.Message):
    """Обробник для повідомлень, що не є фото."""
    await message.answer(
        "Будь ласка, завантажте фото для постеру або /skip. "
        "Інші типи повідомлень не приймаються.",
        reply_markup=SKIP_AND_CANCEL_BUTTONS,
    )


@staff_router.message(CreateTraining.waiting_for_distance)
async def process_training_distance(message: types.Message, state: FSMContext):
    """Обробник введення дистанції тренування."""
    try:
        distance_str = message.text.strip().replace(",", ".")
        distance = float(distance_str)

        if not validators.validate_distance(distance):
            await message.answer(
                "Дистанція повинна бути більше "
                f"{validators.MIN_DISTANCE} км та не більше {validators.MAX_DISTANCE} км. "
                "Спробуйте ще раз:"
            )
            return

        # Перевіряємо, чи не дублюється дистанція
        data = await state.get_data()
        existing_distances = [d["distance"] for d in data.get("distances", [])]
        if distance in existing_distances:
            await message.answer(
                f"Дистанція {distance} км вже додана. Введіть іншу дистанцію:"
            )
            return

        await state.update_data(current_distance=distance)
        await state.set_state(CreateTraining.waiting_for_max_participants)
        await message.answer(
            f"Дистанція {distance} км.\n"
            "Введіть максимальну кількість учасників для цієї дистанції "
            "(введіть 0 для необмеженої кількості):"
        )
    except ValueError:
        await message.answer(
            "Некоректний формат дистанції. Введіть число (наприклад, 5 або 10.5):"
        )


@staff_router.message(CreateTraining.waiting_for_max_participants)
async def process_max_participants(message: types.Message, state: FSMContext):
    """Обробник введення максимальної кількості учасників."""
    try:
        max_participants = int(message.text.strip())

        if not validators.validate_participants(max_participants):
            await message.answer(
                f"Кількість учасників повинна бути від 0 до {validators.MAX_PARTICIPANTS}. "
                "Спробуйте ще раз:"
            )
            return

        await state.update_data(current_max_participants=max_participants)
        await state.set_state(CreateTraining.waiting_for_pace_min)
        await message.answer(
            "Введіть мінімальний (повільний) темп у форматі ХХ:СС "
            "(наприклад, 07:30) або /skip для пропуску:",
            reply_markup=SKIP_AND_CANCEL_BUTTONS,
        )
    except ValueError:
        await message.answer(
            "Некоректний формат кількості учасників. Введіть ціле число:"
        )


@staff_router.message(
    CreateTraining.waiting_for_pace_min,
    lambda message: message.text in {"/skip", mt.btn_skip},
)
async def skip_pace_min(message: types.Message, state: FSMContext):
    """Пропуск мінімального темпу."""
    await state.update_data(current_pace_min=None)
    await state.set_state(CreateTraining.waiting_for_pace_max)
    await message.answer(
        "Введіть максимальний (швидкий) темп у форматі ХХ:СС "
        "(наприклад, 03:30) або /skip для пропуску:",
        reply_markup=SKIP_AND_CANCEL_BUTTONS,
    )


@staff_router.message(CreateTraining.waiting_for_pace_min)
async def process_pace_min(message: types.Message, state: FSMContext):
    """Обробник введення мінімального темпу."""
    pace_str = parse_pace(message.text)

    if not validators.validate_pace(pace_str):
        await message.answer(
            "Темп повинен бути між "
            f"{validators.MIN_PACE_SECONDS//60:02d}:{validators.MIN_PACE_SECONDS%60:02d} "
            f"та {validators.MAX_PACE_SECONDS//60:02d}:{validators.MAX_PACE_SECONDS%60:02d} хв/км. "
            "Спробуйте ще раз:"
        )
        return

    await state.update_data(current_pace_min=pace_str)
    await state.set_state(CreateTraining.waiting_for_pace_max)
    await message.answer(
        "Введіть максимальний (швидкий) темп у форматі ХХ:СС "
        "(наприклад, 03:30) або /skip для пропуску:",
        reply_markup=SKIP_AND_CANCEL_BUTTONS,
    )


@staff_router.message(
    CreateTraining.waiting_for_pace_max,
    lambda message: message.text in {"/skip", mt.btn_skip},
)
async def skip_pace_max(message: types.Message, state: FSMContext):
    """Пропуск максимального темпу."""
    await state.update_data(current_pace_max=None)
    await state.set_state(CreateTraining.waiting_for_route_gpx)
    await message.answer(
        "Додайте файл маршруту в форматі .GPX, або /skip:",
        reply_markup=SKIP_AND_CANCEL_BUTTONS,
    )


@staff_router.message(CreateTraining.waiting_for_pace_max)
async def process_pace_max(message: types.Message, state: FSMContext):
    """Обробник введення максимального темпу."""
    pace_str = parse_pace(message.text)

    if not validators.validate_pace(pace_str):
        await message.answer(
            "Темп повинен бути між "
            f"{validators.MIN_PACE_SECONDS//60:02d}:{validators.MIN_PACE_SECONDS%60:02d} "
            f"та {validators.MAX_PACE_SECONDS//60:02d}:{validators.MAX_PACE_SECONDS%60:02d} хв/км. "
            "Спробуйте ще раз:"
        )
        return

    # Перевіряємо, що максимальний темп не менший за мінімальний
    data = await state.get_data()
    if data.get("current_pace_min"):
        min_pace = datetime.strptime(data["current_pace_min"], "%M:%S").time()
        max_pace = datetime.strptime(pace_str, "%M:%S").time()

        min_seconds = min_pace.minute * 60 + min_pace.second
        max_seconds = max_pace.minute * 60 + max_pace.second

        if max_seconds > min_seconds:
            await message.answer(
                f"Максимальний (швидкий) темп ({pace_str}) не може бути "
                f"повільніше за мінімальний (повільний) ({data['current_pace_min']}). "
                "Спробуйте ще раз:"
            )
            return

    await state.update_data(current_pace_max=pace_str)
    await state.set_state(CreateTraining.waiting_for_route_gpx)
    await message.answer(
        "Додайте файл маршруту в форматі .GPX, або /skip:",
        reply_markup=SKIP_AND_CANCEL_BUTTONS,
    )


@staff_router.message(
    CreateTraining.waiting_for_route_gpx,
    lambda message: message.text in {"/skip", mt.btn_skip},
)
async def skip_route_gpx(message: types.Message, state: FSMContext):
    """Пропуск додавання файлу маршруту."""
    await state.update_data(
        current_route_gpx=None, current_source_filename_gpx=None
    )
    await save_current_distance_and_ask_next(message, state)


@staff_router.message(
    CreateTraining.waiting_for_route_gpx, F.document.file_name.endswith(".gpx")
)
async def process_route_gpx(message: types.Message, state: FSMContext):
    """Обробник введення файлу маршруту."""
    data = await state.get_data()
    existing_route_gpx = [
        d.get("source_filename_gpx") for d in data.get("distances", [])
    ]

    filename = message.document.file_name
    if filename in existing_route_gpx:
        await message.answer(
            f"Цей файл {filename} маршруту вже був доданий до цього тренування. "
            "Спробуйте ще раз або /skip для пропуску:"
        )
        return

    await state.update_data(
        current_route_gpx=message.document.file_id,
        current_source_filename_gpx=filename,
    )
    await message.answer("Маршрут успішно додано.", reply_markup=CANCEL_BUTTON)
    await save_current_distance_and_ask_next(message, state)


@staff_router.message(CreateTraining.waiting_for_route_gpx)
async def invalid_route_gpx(message: types.Message):
    """Обробник некоректного файлу маршруту."""
    await message.answer(
        "Некоректний формат файлу маршруту. "
        "Файл повинен бути у форматі .GPX. Спробуйте ще раз "
        "або /skip для пропуску:",
        reply_markup=SKIP_AND_CANCEL_BUTTONS,
    )


async def save_current_distance_and_ask_next(
    message: types.Message, state: FSMContext
):
    """Зберігає поточну дистанцію та пропонує додати наступну."""
    data = await state.get_data()
    distances = data.get("distances", [])

    # Додаємо поточну дистанцію до списку
    current_distance = {
        "distance": data["current_distance"],
        "max_participants": data["current_max_participants"],
        "pace_min": data.get("current_pace_min"),
        "pace_max": data.get("current_pace_max"),
        "route_gpx": data.get("current_route_gpx"),
        "source_filename_gpx": data.get("current_source_filename_gpx"),
    }
    distances.append(current_distance)

    # Показуємо всі додані дистанції
    distances_text = format_distances_list(distances)
    keyboard = kb.add_distance_or_finish_keyboard()

    await state.update_data(distances=distances)
    await message.answer(
        f"✅ Дистанція {current_distance['distance']} км додана!\n\n"
        f"📏 Додані дистанції:\n{distances_text}\n\n"
        f"Що робимо далі?",
        reply_markup=keyboard,
    )


def format_distances_list(distances: list) -> str:
    """Форматує список дистанцій для відображення."""
    return "\n".join(
        [
            f"• {d['distance']} км - макс. {('необмежено' if d['max_participants'] == 0 else str(d['max_participants']))} учасників"
            + format_pace_info(d)
            + format_route_info(d)
            for d in distances
        ]
    )


def format_pace_info(distance_data: dict) -> str:
    """Форматує інформацію про темп."""
    if not distance_data.get("pace_min") and not distance_data.get("pace_max"):
        return ""

    pace_parts = []
    if distance_data.get("pace_min"):
        pace_parts.append(f"від {distance_data['pace_min']}")
    if distance_data.get("pace_max"):
        pace_parts.append(f"до {distance_data['pace_max']}")

    return f" (темп: {' '.join(pace_parts)})"


def format_route_info(distance_data: dict) -> str:
    """Форматує інформацію про маршрут."""
    return " (маршрут: 🗺)" if distance_data.get("route_gpx") else ""


@staff_router.callback_query(F.data == "add_distance")
async def add_another_distance(
    callback: types.CallbackQuery, state: FSMContext
):
    """Додавання ще однієї дистанції."""

    # Очищуємо поточні дані дистанції
    data = await state.get_data()
    current_keys = [key for key in data.keys() if key.startswith("current_")]

    for key in current_keys:
        data.pop(key, None)

    await state.set_data(data)
    await state.set_state(CreateTraining.waiting_for_distance)

    await callback.message.edit_text(
        "Введіть наступну дистанцію (у кілометрах):"
    )
    await callback.answer()


@staff_router.callback_query(F.data == "finish_training")
async def finish_training_creation(
    callback: types.CallbackQuery, state: FSMContext
):
    """Завершення створення тренування."""
    await callback.message.edit_text("⏳ Створюю тренування...")
    await callback.bot.send_chat_action(
        callback.message.chat.id, action="typing"
    )
    await create_training_final(callback.message, state)
    await callback.answer()


# async def download_file_safe(bot, file_id: str, destination: str) -> bool:
#     """Безпечно завантажує файл."""
#     try:
#         file = await bot.get_file(file_id)
#         await bot.download_file(
#             file_path=file.file_path, destination=destination
#         )
#         return True
#     except Exception as e:
#         logger.error(f"Помилка завантаження файлу {file_id}: {e}")
#         return False
#
#
# async def create_poster_path(
#     club_user_id: int, file_id: str, bot
# ) -> Optional[str]:
#     """Створює шлях для постера та завантажує його."""
#     try:
#         file = await bot.get_file(file_id)
#         file_name = file.file_path.split("/")[-1]
#         save_path = (
#             Path(settings.MEDIA_ROOT) / f"trainings/{club_user_id}/images"
#         )
#         save_path.mkdir(parents=True, exist_ok=True)
#
#         poster_path = save_path / file_name
#
#         if await download_file_safe(bot, file_id, str(poster_path)):
#             return str(poster_path)
#         return None
#     except Exception as e:
#         logger.error(f"Помилка створення шляху постера: {e}")
#         return None
#
#
# async def create_route_path(
#     club_user_id: int,
#     distance: float,
#     training_date: datetime,
#     file_id: str,
#     bot: Bot,
# ) -> tuple[Optional[str], Optional[str]]:
#     """Створює шлях для маршруту та завантажує його."""
#     try:
#         file = await bot.get_file(file_id)
#         file_extension = file.file_path.split("/")[-1].split(".")[-1]
#         file_name = f"{distance}km_{training_date.strftime('%d%B%Y_%H%M')}.{file_extension}"
#
#         save_path = Path(settings.MEDIA_ROOT) / f"trainings/{club_user_id}/gpx"
#         save_path.mkdir(parents=True, exist_ok=True)
#
#         route_path = save_path / file_name
#
#         if await download_file_safe(bot, file_id, str(route_path)):
#             map_image_path = str(route_path).replace(".gpx", ".png")
#             # Запускаємо Celery-задачу асинхронно
#             visualize_gpx.delay(
#                 gpx_file=str(route_path), output_file=map_image_path
#             )
#             return str(route_path), map_image_path
#         return None, None
#     except Exception as e:
#         logger.error(f"Помилка створення шляху маршруту: {e}")
#         return None, None


async def create_training_final(message: types.Message, state: FSMContext):
    """Фінальне створення тренування та всіх дистанцій."""
    data = await state.get_data()

    try:
        # Отримуємо користувача, який створює тренування
        club_user = await get_club_user(message.chat.id)
        if not club_user:
            await clear_state_and_notify(
                message,
                state,
                "❌ Помилка: Ваш обліковий запис не знайдено в системі. "
                "Зверніться до адміністратора.",
            )
            return

        # Створюємо datetime
        training_datetime = timezone.make_aware(
            datetime.combine(
                datetime.strptime(data["date"], "%d.%m.%Y").date(),
                datetime.strptime(data["time"], "%H:%M").time(),
            )
        )

        # Завантаження постера
        poster_path = None
        if data.get("poster_file_id"):
            poster_path = await create_poster_path(
                club_user.id, data["poster_file_id"], message.bot
            )

        # Створюємо функцію для транзакції
        @sync_to_async
        def create_training_with_distances():
            with transaction.atomic():
                # Створюємо тренування
                training = TrainingEvent.objects.create(
                    title=data["title"],
                    description=data.get("description", ""),
                    date=training_datetime,
                    location=data["location"],
                    poster=(
                        poster_path.replace(str(settings.MEDIA_ROOT), "")
                        if poster_path
                        else None
                    ),
                    created_by=club_user,
                )

                # Створюємо дистанції
                created_distances = []
                for distance_data in data["distances"]:
                    # Обробка маршруту GPX (цю частину залишаємо async)
                    training_distance = TrainingDistance.objects.create(
                        training=training,
                        distance=distance_data["distance"],
                        max_participants=distance_data["max_participants"],
                        pace_min=distance_data.get("pace_min"),
                        pace_max=distance_data.get("pace_max"),
                        route_gpx=None,  # Встановимо пізніше
                        route_gpx_map=None,  # Встановимо пізніше
                    )
                    created_distances.append(
                        {
                            "distance_obj": training_distance,
                            "distance_data": distance_data,
                        }
                    )

                return training, created_distances

        # Виконуємо транзакцію
        training, created_distances_info = (
            await create_training_with_distances()
        )

        # # Обробляємо GPX файли після створення записів в БД
        # created_distances = []
        # for info in created_distances_info:
        #     distance_obj = info["distance_obj"]
        #     distance_data = info["distance_data"]
        #
        #     # Обробка маршруту GPX
        #     if distance_data.get("route_gpx"):
        #         route_path, map_image_path = await create_route_path(
        #             club_user.id,
        #             distance_data["distance"],
        #             training_datetime,
        #             distance_data["route_gpx"],
        #             message.bot,
        #         )
        #
        #         # Оновлюємо шляхи в базі даних
        #         if route_path or map_image_path:
        #             await sync_to_async(
        #                 lambda: setattr(
        #                     distance_obj,
        #                     "route_gpx",
        #                     (
        #                         route_path.replace(
        #                             str(settings.MEDIA_ROOT), ""
        #                         )
        #                         if route_path
        #                         else None
        #                     ),
        #                 )
        #             )()
        #             await sync_to_async(
        #                 lambda: setattr(
        #                     distance_obj,
        #                     "route_gpx_map",
        #                     (
        #                         map_image_path.replace(
        #                             str(settings.MEDIA_ROOT), ""
        #                         )
        #                         if map_image_path
        #                         else None
        #                     ),
        #                 )
        #             )()
        #             await sync_to_async(distance_obj.save)()
        #
        #     created_distances.append(distance_obj)

        # Обробляємо GPX файли після створення записів в БД
        created_distances = await process_gpx_files_after_creation(
            created_distances_info,
            club_user.id,
            training_datetime,
            message.bot,
        )

        # Формуємо повідомлення про успішне створення
        success_message = mt.format_success_message(
            training, created_distances
        )

        # Очищаємо FSM та надсилаємо повідомлення видаляємо попереднє повідомлення
        await clear_state_and_notify(message, state, success_message, True)

        logger.info(
            "Тренування %s успішно створено користувачем %s",
            training.id,
            club_user.id,
        )

    except ValidationError as e:
        logger.error("Помилка валідації при створенні тренування: %s", e)
        await clear_state_and_notify(
            message,
            state,
            "❌ Помилка валідації даних. Спробуйте створити тренування знову.",
        )
    except Exception as e:
        logger.error("Помилка створення тренування: %s", e)
        await clear_state_and_notify(
            message,
            state,
            "❌ Виникла помилка при створенні тренування. "
            "Спробуйте пізніше або зверніться до адміністратора.",
        )
