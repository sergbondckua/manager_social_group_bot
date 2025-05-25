from datetime import datetime

from aiogram import Router, F
from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from django.utils import timezone
from django.core.exceptions import ValidationError

from profiles.models import ClubUser
from robot.tgbot.filters.staff import ClubStaffFilter
from robot.tgbot.keyboards.staff import add_distance_or_finish_keyboard
from robot.tgbot.states.staff import CreateTraining
from robot.tgbot.text import staff_create_training as mt
from training_events.models import TrainingEvent, TrainingDistance

staff_router = Router()
staff_router.message.filter(ClubStaffFilter())


# Додатковий обробник для скасування створення тренування
@staff_router.message(Command("cancel"))
async def cancel_training_creation(message: types.Message, state: FSMContext):
    """Скасування створення тренування."""

    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Немає активного процесу, який можна скасувати.")
        return

    await state.clear()
    await message.answer("❌ Створення тренування скасовано.")


@staff_router.message(Command("create_training"))
async def cmd_create_training(message: types.Message, state: FSMContext):
    """Обробник команди "/create_training"."""

    await state.set_state(CreateTraining.waiting_for_title)
    await message.answer("Введіть назву тренування:")


@staff_router.message(CreateTraining.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    """Обробник введення назви тренування."""

    # Перевіряємо довжину назви
    if len(message.text.strip()) < 3:
        await message.answer(
            "Назва тренування занадто коротка. Введіть принаймні 3 символи:"
        )
        return

    if len(message.text.strip()) > 200:
        await message.answer(
            "Назва тренування занадто довга. Максимум 200 символів:"
        )
        return

    await state.update_data(title=message.text.strip())
    await state.set_state(CreateTraining.waiting_for_description)
    await message.answer("Введіть опис тренування (або /skip для пропуску):")


@staff_router.message(
    CreateTraining.waiting_for_description, F.text == "/skip"
)
async def skip_description(message: types.Message, state: FSMContext):
    """Пропуск опису тренування."""

    await state.update_data(description="")
    await state.set_state(CreateTraining.waiting_for_date)
    await message.answer("Введіть дату тренування у форматі ДД.ММ.РРРР:")


@staff_router.message(CreateTraining.waiting_for_description)
async def process_training_description(
    message: types.Message, state: FSMContext
):
    """Обробник введення опису тренування."""

    await state.update_data(description=message.text.strip())
    await state.set_state(CreateTraining.waiting_for_date)
    await message.answer("Введіть дату тренування у форматі ДД.ММ.РРРР:")


@staff_router.message(CreateTraining.waiting_for_date)
async def process_training_date(message: types.Message, state: FSMContext):
    """Обробник введення дати тренування."""

    try:
        date_str = (
            message.text.strip()
            .replace("/", ".")
            .replace(",", ".")
            .replace(" ", ".")
        )

        parsed_date = datetime.strptime(date_str, "%d.%m.%Y")

        # Перевіряємо, що дата не в минулому
        if parsed_date.date() < timezone.now().date():
            await message.answer(
                "Дата тренування не може бути в минулому. Введіть коректну дату:"
            )
            return

        await state.update_data(date=date_str)
        await state.set_state(CreateTraining.waiting_for_time)
        await message.answer("Введіть час тренування у форматі ГГ:ММ:")

    except ValueError:
        await message.answer(
            "Некоректний формат дати. "
            "Введіть дату у форматі ДД.ММ.РРРР (наприклад, 25.12.2025):"
        )


@staff_router.message(CreateTraining.waiting_for_time)
async def process_training_time(message: types.Message, state: FSMContext):
    """Обробник введення часу тренування."""

    try:
        time_str = (
            message.text.strip()
            .replace("/", ":")
            .replace(",", ":")
            .replace(" ", ":")
            .replace(".", ":")
        )

        # Перевіряємо формат часу
        parsed_time = datetime.strptime(time_str, "%H:%M").time()

        # Додаткова перевірка на коректність часу для сьогоднішньої дати
        data = await state.get_data()
        training_date = datetime.strptime(data["date"], "%d.%m.%Y").date()
        training_datetime = datetime.combine(training_date, parsed_time)

        if training_datetime < datetime.now():
            await message.answer(
                "Час тренування не може бути в минулому. Введіть коректний час:"
            )
            return

        await state.update_data(time=time_str)
        await state.set_state(CreateTraining.waiting_for_location)
        await message.answer("Введіть місце зустрічі для тренування:")

    except ValueError:
        await message.answer(
            "Некоректний формат часу. Введіть час у форматі ГГ:ММ (наприклад, 08:30):"
        )


@staff_router.message(CreateTraining.waiting_for_location)
async def process_training_location(message: types.Message, state: FSMContext):
    """Обробник введення місця тренування."""

    location = message.text.strip()
    if len(location) < 3:
        await message.answer(
            "Місце зустрічі занадто коротке. Введіть принаймні 3 символи:"
        )
        return

    if len(location) > 300:
        await message.answer(
            "Місце зустрічі занадто довге. Максимум 300 символів:"
        )
        return

    await state.update_data(location=location, distances=[])
    await state.set_state(CreateTraining.waiting_for_poster)
    await message.answer("Завантажте постер тренування (фото) або /skip:")


@staff_router.message(
    CreateTraining.waiting_for_poster, F.photo | F.document | F.text == "/skip"
)
async def process_training_poster(message: types.Message, state: FSMContext):
    """Обробник введення постеру тренування."""

    if message.text == "/skip":
        await state.set_state(CreateTraining.waiting_for_distance)
        await message.answer(
            "Тепер додамо дистанції для тренування.\n"
            "Введіть першу дистанцію (у кілометрах):"
        )
        return

    file_id = None
    # Обробка фото
    if message.photo:
        file_id = message.photo[-1].file_id
    # Обробка документу-зображення
    elif message.document and message.document.mime_type.startswith("image/"):
        file_id = message.document.file_id

    if not file_id:
        await message.answer(
            "Будь ласка, завантажте зображення у підтримуваному форматі."
        )
        return

    await state.update_data(poster_file_id=file_id)
    await state.set_state(CreateTraining.waiting_for_distance)
    await message.answer("Введіть першу дистанцію (у кілометрах):")


@staff_router.message(CreateTraining.waiting_for_distance)
async def process_training_distance(message: types.Message, state: FSMContext):
    """Обробник введення дистанції тренування."""

    try:
        distance_str = message.text.strip().replace(",", ".")
        distance = float(distance_str)

        if distance <= 1:
            await message.answer(
                "Дистанція повинна бути більше 1 км. Спробуйте ще раз:"
            )
            return

        if distance > 100:
            await message.answer(
                "Дистанція занадто велика (максимум 100 км). Спробуйте ще раз:"
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
        if max_participants < 0:
            await message.answer(
                "Кількість учасників не може бути від'ємною. Спробуйте ще раз:"
            )
            return

        if max_participants > 100:
            await message.answer(
                "Кількість учасників занадто велика (максимум 100). "
                "Спробуйте ще раз:"
            )
            return

        await state.update_data(current_max_participants=max_participants)
        await state.set_state(CreateTraining.waiting_for_pace_min)
        await message.answer(
            "Введіть мінімальний (швидкий) темп у форматі ХХ:СС "
            "(наприклад, 03:30) або /skip для пропуску:"
        )
    except ValueError:
        await message.answer(
            "Некоректний формат кількості учасників. Введіть ціле число:"
        )


@staff_router.message(CreateTraining.waiting_for_pace_min, F.text == "/skip")
async def skip_pace_min(message: types.Message, state: FSMContext):
    """Пропуск мінімального темпу."""

    await state.update_data(current_pace_min=None)
    await state.set_state(CreateTraining.waiting_for_pace_max)
    await message.answer(
        "Введіть максимальний (повільний) темп у форматі ХХ:СС "
        "(наприклад, 06:30) або /skip для пропуску:"
    )


@staff_router.message(CreateTraining.waiting_for_pace_min)
async def process_pace_min(message: types.Message, state: FSMContext):
    """Обробник введення мінімального темпу."""

    try:
        pace_str = message.text.strip().replace(".", ":").replace(",", ":")
        parsed_pace = datetime.strptime(pace_str, "%M:%S").time()

        # Перевіряємо розумність темпу (від 3:00 до 15:00 хв/км)
        total_seconds = parsed_pace.minute * 60 + parsed_pace.second
        if total_seconds < 180 or total_seconds > 900:
            await message.answer(
                "Темп повинен бути між 03:00 та 15:00 хв/км. Спробуйте ще раз:"
            )
            return

        await state.update_data(current_pace_min=pace_str)
        await state.set_state(CreateTraining.waiting_for_pace_max)
        await message.answer(
            "Введіть максимальний (повільний) темп у форматі ХХ:СС "
            "(наприклад, 06:30) або /skip для пропуску:"
        )
    except ValueError:
        await message.answer(
            "Некоректний формат темпу. "
            "Введіть темп у форматі ХХ:СС (наприклад, 05:30) або /skip:"
        )


@staff_router.message(CreateTraining.waiting_for_pace_max, F.text == "/skip")
async def skip_pace_max(message: types.Message, state: FSMContext):
    """Пропуск максимального темпу."""

    await state.update_data(current_pace_max=None)
    await state.set_state(CreateTraining.waiting_for_route_gpx)
    await message.answer("Введіть маршрут у форматі GPX або /skip для пропуску:")


@staff_router.message(CreateTraining.waiting_for_pace_max)
async def process_pace_max(message: types.Message, state: FSMContext):
    """Обробник введення максимального темпу."""

    try:
        pace_str = message.text.strip().replace(".", ":").replace(",", ":")
        parsed_pace = datetime.strptime(pace_str, "%M:%S").time()

        # Перевіряємо розумність темпу
        total_seconds = parsed_pace.minute * 60 + parsed_pace.second
        if total_seconds < 180 or total_seconds > 900:
            await message.answer(
                "Темп повинен бути між 03:00 та 15:00 хв/км. Спробуйте ще раз:"
            )
            return

        # Перевіряємо, що максимальний темп не менший за мінімальний
        data = await state.get_data()
        if data.get("current_pace_min"):
            min_pace = datetime.strptime(
                data["current_pace_min"], "%M:%S"
            ).time()
            min_seconds = min_pace.minute * 60 + min_pace.second
            if total_seconds < min_seconds:
                await message.answer(
                    f"Максимальний (повільний) темп ({pace_str}) не може бути "
                    f"швидшим за мінімальний (швидкий) ({data['current_pace_min']}). "
                    "Спробуйте ще раз:"
                )
                return

        await state.update_data(current_pace_max=pace_str)
        await state.set_state(CreateTraining.waiting_for_route_gpx)
        await message.answer(
            "Додайте файл маршруту в форматі .GPX, або /skip:"
        )
    except ValueError:
        await message.answer(
            "Некоректний формат темпу. Введіть темп у форматі ХХ:СС (наприклад, 06:30) або /skip:"
        )


@staff_router.message(CreateTraining.waiting_for_route_gpx, F.text == "/skip")
async def skip_route_gpx(message: types.Message, state: FSMContext):
    """Пропуск додавання файлу маршруту."""

    await state.update_data(сurrent_route_gpx=None)
    await save_current_distance_and_ask_next(message, state)


@staff_router.message(CreateTraining.waiting_for_route_gpx, F.document)
async def process_route_gpx(message: types.Message, state: FSMContext):
    """Обробник введення файлу маршруту."""

    try:
        if message.document and message.document.file_name.endswith(".gpx"):
            await state.update_data(сurrent_route_gpx=message.document.file_id)
        else:
            await message.answer("Будь ласка, завантажте файл у форматі .gpx")
            return

        await save_current_distance_and_ask_next(message, state)
    except ValueError:
        await message.answer(
            "Некоректний формат файлу маршруту. Спробуйте ще раз:"
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
    }
    distances.append(current_distance)

    # Показуємо всі додані дистанції
    distances_text = "\n".join(
        [
            f"• {d['distance']} км - макс. {('необмежено' if d['max_participants'] == 0 else str(d['max_participants']))} учасників"
            + (
                f" (темп: "
                + " ".join(
                    [
                        f"від {d['pace_min']}" if d["pace_min"] else "",
                        f"до {d['pace_max']}" if d["pace_max"] else "",
                    ]
                ).strip()
                + ")"
                if d["pace_min"] or d["pace_max"]
                else ""
            )
            + (f" (маршрут: 🗺)" if d["route_gpx"] else "-")
            for d in distances
        ]
    )

    # Створюємо клавіатуру
    keyboard = add_distance_or_finish_keyboard()

    await state.update_data(distances=distances)
    await message.answer(
        f"✅ Дистанція {current_distance['distance']} км додана!\n\n"
        f"📏 Додані дистанції:\n{distances_text}\n\n"
        "Що робити далі?",
        reply_markup=keyboard,
    )


@staff_router.callback_query(F.data == "add_distance")
async def add_another_distance(
    callback: types.CallbackQuery, state: FSMContext
):
    """Додавання ще однієї дистанції."""

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
    await create_training_final(callback.message, state)
    await callback.answer()


async def create_training_final(message: types.Message, state: FSMContext):
    """Фінальне створення тренування та всіх дистанцій."""

    data = await state.get_data()

    try:
        # Отримуємо користувача, який створює тренування
        club_user = await ClubUser.objects.aget(telegram_id=message.chat.id)

        # Створюємо datetime
        training_datetime = timezone.make_aware(
            datetime.combine(
                datetime.strptime(data["date"], "%d.%m.%Y").date(),
                datetime.strptime(data["time"], "%H:%M").time(),
            )
        )

        # Перевіряємо унікальність назви тренування
        if await TrainingEvent.objects.filter(title=data["title"]).aexists():
            await message.answer(
                f"❌ Тренування з назвою '{data['title']}' вже існує. "
                "Оберіть іншу назву і спробуйте ще раз."
            )
            await state.clear()
            return

        # Завантаження постера
        poster_path = None
        if data.get("poster_file_id"):
            try:
                file = await message.bot.get_file(data["poster_file_id"])
                poster_path = TrainingEvent.get_upload_path(
                    TrainingEvent(), file.file_path.split("/")[-1]
                )
                await message.bot.download_file(
                    file.file_path, f"media/{poster_path}"
                )
            except Exception as e:
                await message.answer(f"Помилка завантаження постера: {e}")

        # Створюємо тренування
        training = await TrainingEvent.objects.acreate(
            title=data["title"],
            description=data.get("description", ""),
            date=training_datetime,
            location=data["location"],
            created_by=club_user,
            poster=poster_path,
        )

        # Створюємо всі дистанції для тренування
        distances_created = []
        for distance_data in data["distances"]:
            # Завантаження маршруту
            route_path = None
            if distance_data.get("route_gpx"):
                try:
                    file = await message.bot.get_file(
                        distance_data["route_gpx"]
                    )
                    route_path = TrainingDistance.get_upload_path(
                        TrainingDistance(), file.file_path.split("/")[-1]
                    )
                    await message.bot.download_file(
                        file.file_path, f"media/{route_path}"
                    )
                except Exception as e:
                    await message.answer(f"Помилка завантаження маршруту: {e}")

            distance = await TrainingDistance.objects.acreate(
                training=training,
                distance=distance_data["distance"],
                pace_min=(
                    datetime.strptime(
                        distance_data["pace_min"], "%M:%S"
                    ).time()
                    if distance_data.get("pace_min")
                    else None
                ),
                pace_max=(
                    datetime.strptime(
                        distance_data["pace_max"], "%M:%S"
                    ).time()
                    if distance_data.get("pace_max")
                    else None
                ),
                max_participants=distance_data["max_participants"],
                route_gpx=route_path,
            )
            distances_created.append(distance)

        # Формуємо повідомлення про створені дистанції
        distances_info = "\n".join(
            [
                f"📏 {d.distance} км - макс. {'необмежено' if d.max_participants == 0 else d.max_participants} учасників"
                + (
                    f"\n   🏃‍♂️ Темп: "
                    + " ".join(
                        [
                            (
                                f"від {d.pace_min.strftime('%M:%S')}"
                                if d.pace_min
                                else ""
                            ),
                            (
                                f"до {d.pace_max.strftime('%M:%S')}"
                                if d.pace_max
                                else ""
                            ),
                        ]
                    ).strip()
                    if d.pace_min or d.pace_max
                    else ""
                    + "\n   📍 Маршрут: "
                    + ("🗺" if d.route_gpx else "-")
                )
                for d in distances_created
            ]
        )

        success_message = (
            f"✅ Тренування успішно створено!\n\n"
            f"📋 Назва: {data['title']}\n"
            f"📝 Опис: {data.get('description', 'Без опису')}\n"
            f"📅 Дата: {training_datetime.strftime('%d.%m.%Y %H:%M')}\n"
            f"📍 Місце: {data['location']}\n\n"
            f"Дистанції:\n{distances_info}"
        )

        await message.answer(success_message)
        await state.clear()

    except ClubUser.DoesNotExist:
        await message.answer(
            "❌ Помилка: Ваш обліковий запис не знайдено в системі. "
            "Зверніться до адміністратора."
        )
        await state.clear()

    except ValidationError as e:
        await message.answer(f"❌ Помилка валідації: {str(e)}")
        await state.clear()

    except Exception as e:
        await message.answer(
            f"❌ Сталася помилка при створенні тренування: {str(e)}"
        )
        await state.clear()
