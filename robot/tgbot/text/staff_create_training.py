from aiogram.utils.markdown import hbold, hcode, hitalic, text
from html import escape

from asgiref.sync import sync_to_async

from common.utils import clean_tag_message
from training_events.models import TrainingEvent

btn_cancel = text("🚫 Скасувати створення")
btn_close = text("❌ Прибрати")
btn_skip = text("⏩ Пропустити")
btn_finish_training = text("🏁 Завершити створення")
btn_add_distance = text("➕ Додати ще дистанцію")
btn_training_publish = text("🗞 Анонсувати")
btn_training_delete = text("🗑 Видалити")
btn_cancel_training = text("🛑 Скасувати анонсоване тренування")
btn_register_training = text("®️ Я, буду!")

format_delete_confirmation = text(
    "⚠️ " + hbold("Підтвердження видалення тренування\n\n"),
    "📌 " + hbold("Назва: ") + "{training_title}\n",
    "🆔 " + hbold("ID: ") + "{training_id}\n",
    "👥 " + hbold("Учасників: ") + "{participants_count}\n\n",
    "🔥 " + hbold("Увага: ця дія незворотна!"),
)

format_revoke_confirmation = text(
    "⚠️ " + hbold("Підтвердження скасування тренування\n\n"),
    "📌 " + hbold("Назва: ") + "{training_title}\n",
    "🆔 " + hbold("ID: ") + "{training_id}\n",
)

format_confirmation_message = text(
    "🎯 ",
    hbold("Дистанція {current_distance} км успішно додана!\n\n"),
    "📊 " + hitalic("Список доданих дистанцій: \n"),
    "{distances_text}\n\n",
    "🛠️ " + hbold("Наступні дії:\n\n"),
    "Оберіть дію з меню нижче 👇",
)

format_training_cancellation_confirmation = text(
    f"✅ " + hbold("Тренування «{training_title}» скасовано!\n\n"),
    "📊 " + hitalic("Деталі:\n"),
    "   • Дата: {training_date}\n",
    "   • Учасників повідомлено: " + hbold("{participants_count}") + " осб.\n",
    "📨 " + hitalic("Всі зареєстровані учасники отримали сповіщення"),
)

format_invalid_file_message = text(
    "❌ " + hbold("Невірний формат файлу!") + "\n\n",
    "📁 Будь ласка, завантажте файл у " + hbold("GPX") + " форматі\n",
    "ℹ️ "
    + "Це стандартний формат для треків з більшості спортивних додатків\n\n",
    "🔄 "
    + "Спробуйте завантажити ще раз або натисніть команду /skip для пропуску",
)

format_training_cancellation_notice = text(
    "🚨 " + hbold("Важливе сповіщення!\n\n"),
    "😔 "
    + hitalic("Тренування ")
    + hbold("{training_title} ")
    + hitalic(", на яке ви зареєстровані,\n"),
    "📅 " + hbold("Дата: ") + "{training_date}\n\n",
    "‼️СКАСОВАНО‼️\n\n",
    "🚧 " + hbold("Причина:") + " адміністративне рішення\n\n",
    "🙏 Вибачте за незручності! Ми повідомимо про нові тренування.",
)

@sync_to_async
def format_success_message(training: TrainingEvent, distances: list) -> str:
    """Форматує повідомлення про успішне створення тренування з HTML-форматуванням"""
    # Основні компоненти повідомлення
    message = [
        f"🏷 {hbold('Назва:')} {escape(training.title)}",
    ]

    # Опис (якщо є)
    if training.description:
        message.append(
            f"📋 {hbold('Опис:')} {clean_tag_message(training.description)}"
        )

    # Постер (якщо є)
    if training.poster:
        message.append(f"\n🖼 {hbold('Постер додано')}")

    # Дата та час
    date_str = training.date.date().strftime("%d.%m.%Y")
    time_str = training.date.time().strftime("%H:%M")
    message.extend(
        [
            f"\n📅 {hbold('Дата:')} {date_str}",
            f"🕒 {hbold('Час:')} {time_str}",
            f"📍 {hbold('Місце:')} {escape(training.location)}",
        ]
    )

    # Дистанції
    if distances:
        message.append(f"\n📏 {hbold('Дистанції:')}")
        for distance in distances:
            distance_line = f"  • {distance.distance} км"

            # Учасники
            participants = (
                "необмежено"
                if not distance.max_participants
                else f"макс. {distance.max_participants}"
            )
            distance_line += f" | 👥 {participants}"

            # Темп
            if distance.pace_min or distance.pace_max:
                pace = []
                if distance.pace_min:
                    pace.append(f"від {distance.pace_min}")
                if distance.pace_max:
                    pace.append(f"до {distance.pace_max}")
                distance_line += f" | 🏃 {hitalic('темп:')} {' '.join(pace)}"

            # Маршрут
            if distance.route_gpx:
                distance_line += " | 🗺 маршрут"

            message.append(distance_line)

    # Інформація про автора
    creator_name = (
        training.created_by.get_full_name()
        or f"користувач (ID: {training.created_by.telegram_id})"
    )
    if training.registrations.count() > 0:
        registrations = (f"\n👥 {hbold('Зареєстровано: ')} "
                         f"{training.registrations.count()} учасник(а / ів)")
    else:
        registrations = ""

    message.extend(
        [
            registrations,
            f"\n👤 {hbold('Організатор:')} {escape(creator_name)}",
            f"🆔 {hbold('ID тренування:')} {hcode(training.id)}",
        ]
    )

    return "\n".join(message)


def format_distances_list(distances: list) -> str:
    """Форматує список дистанцій з Markdown, емодзі та професійним оформленням."""
    distance_lines = []

    for d in distances:
        # Основний блок: дистанція та учасники
        distance_emoji = "📏"
        distance_text = f"{distance_emoji} {hbold(d['distance'])} км"

        participants_emoji = "👥"
        participants_text = (
            f"{participants_emoji} {hbold('необмежено')} учасників"
            if d["max_participants"] == 0
            else f"{participants_emoji} до {hbold(d['max_participants'])} учасників"
        )

        # Додаткові блоки: темп та маршрут
        pace_info = format_pace_info(d)
        route_info = format_route_info(d)  # Припускаємо наявність цієї функції

        # Збираємо всі компоненти
        components = [
            text(distance_text, "•", participants_text),
            pace_info,
            route_info,
        ]

        # Фільтруємо порожні значення та об'єднуємо
        filtered_components = [c for c in components if c]
        distance_lines.append("\n".join(filtered_components))

    return "\n\n".join(distance_lines)


def format_pace_info(distance_data: dict) -> str:
    """Генерує Markdown-форматовану інформацію про темп з емодзі"""
    pace_min = distance_data.get("pace_min")
    pace_max = distance_data.get("pace_max")

    if not pace_min and not pace_max:
        return ""

    # Емодзі для різних варіантів темпу
    emoji = "🏃💨" if pace_min and pace_max else "⏱️"

    parts = []
    if pace_min:
        parts.append(f"від {hbold(pace_min)}")
    if pace_max:
        parts.append(f"до {hbold(pace_max)}")

    pace_range = " ".join(parts)
    return text(hitalic(f"{emoji} Темп: "), pace_range, hitalic(" хв/км"))


def format_route_info(distance_data: dict) -> str:
    """Форматує інформацію про маршрут з емодзі."""
    if not distance_data.get("route_name"):
        return ""

    emoji = "🗺️"
    return text(hitalic(f"{emoji} Маршрут: "), distance_data["route_name"])
