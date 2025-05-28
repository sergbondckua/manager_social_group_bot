from aiogram.utils.markdown import hbold, hcode, hitalic, text
from html import escape
from training_events.models import TrainingEvent

btn_cancel = text("🚫 Скасувати створення")
btn_skip = text("⏩ Пропустити")
btn_finish_training = text("🏁 Завершити створення")
btn_add_distance = text("➕ Додати ще дистанцію")


def format_success_message(training: TrainingEvent, distances: list) -> str:
    """Форматує повідомлення про успішне створення тренування з HTML-форматуванням"""
    # Основні компоненти повідомлення
    message = [
        f"✨ {hbold('Тренування успішно створено!')} ✨",
        "",
        f"🏷 {hbold('Назва:')} {escape(training.title)}",
    ]

    # Опис (якщо є)
    if training.description:
        message.append(f"📋 {hbold('Опис:')}\n{escape(training.description)}")

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
            f"📍 {hbold('Місце:')}\n{escape(training.location)}",
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
    message.extend(
        [
            f"\n👤 {hbold('Організатор:')} {escape(creator_name)}",
            f"🆔 {hbold('ID тренування:')} {hcode(training.id)}",
        ]
    )

    return "\n".join(message)
