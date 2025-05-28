import logging
from datetime import datetime
from typing import Optional

from aiogram import types, Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction

from profiles.models import ClubUser
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
    keyboard: types = None,
):
    """Очищує стан та надсилає повідомлення."""
    await state.clear()
    # Видалення попереднього повідомлення
    if prev_delete_message:
        await message.delete()
    await message.answer(text, reply_markup=keyboard)


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
        mt.format_invalid_file_message,
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
    distances_text = mt.format_distances_list(distances)
    keyboard = kb.add_distance_or_finish_keyboard()

    await state.update_data(distances=distances)
    await message.answer(
        mt.format_confirmation_message.format(
            current_distance=current_distance["distance"],
            distances_text=distances_text,
        ),
        reply_markup=keyboard,
    )


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
                training_event = TrainingEvent.objects.create(
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
                created_distance_records = []
                for distance_data in data["distances"]:
                    # Обробка маршруту GPX
                    training_distance = TrainingDistance.objects.create(
                        training=training_event,
                        distance=distance_data["distance"],
                        max_participants=distance_data["max_participants"],
                        pace_min=distance_data.get("pace_min"),
                        pace_max=distance_data.get("pace_max"),
                        route_gpx=None,  # Встановимо пізніше
                        route_gpx_map=None,  # Встановимо пізніше
                    )
                    created_distance_records.append(
                        {
                            "distance_obj": training_distance,
                            "distance_data": distance_data,
                        }
                    )

                return training_event, created_distance_records

        # Виконуємо транзакцію
        training, created_distances_info = (
            await create_training_with_distances()
        )

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
        # Клавіатура для публікації тренування
        keyboard = kb.create_training_publish_and_delete_keyboard(training.id)

        # Очищаємо FSM та надсилаємо повідомлення видаляємо попереднє повідомлення
        await clear_state_and_notify(
            message=message,
            state=state,
            text=f"✨ Тренування {training.title} успішно створено! ✨",
            prev_delete_message=True,
            keyboard=types.ReplyKeyboardRemove(),
        )
        await message.answer(success_message, reply_markup=keyboard)

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


@staff_router.callback_query(F.data.startswith("delete_training_"))
async def delete_training_event(callback: types.CallbackQuery):
    """Обробка кнопки Видалення тренування."""

    try:
        # Отримання ID тренування з callback даних
        training_id = int(callback.data.split("_")[-1])

        # Отримання тренування
        training = await TrainingEvent.objects.aget(id=training_id)

        # Видалення тренування
        await training.adelete()
        new_text = f"🗑 Тренування '{training.title}' (ID: {training_id}) успішно видалено!"

        try:
            # Редагування повідомлення
            await callback.message.edit_text(
                text=new_text, reply_markup=None  # Remove inline keyboard
            )
        except TelegramBadRequest:
            # Якщо повідомлення вже було видалено
            await callback.answer(new_text, show_alert=True)
    except TrainingEvent.DoesNotExist:
        await callback.answer("❌ Тренування не знайдено!", show_alert=True)
    except (ValueError, IndexError):
        await callback.answer("❌ Невірний формат команди!", show_alert=True)
    except Exception as e:
        logger.error(f"Delete training error: {e}")
        await callback.answer("🚫 Сталася невідома помилка!", show_alert=True)
    finally:
        # Відповідь на callback
        await callback.answer()
