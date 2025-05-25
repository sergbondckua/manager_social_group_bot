from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram import types


def add_distance_or_finish_keyboard():
    """Інлайн-клавіатура для вибору дистанції або завершення."""
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="➕ Додати ще дистанцію", callback_data="add_distance"
        ),
        types.InlineKeyboardButton(
            text="🏁 Завершити створення",
            callback_data="finish_training",
        ),
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)
