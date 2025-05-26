from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram import types

from robot.tgbot.text import staff_create_training as mt


def add_distance_or_finish_keyboard():
    """Інлайн-клавіатура для вибору дистанції або завершення."""
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text=mt.btn_add_distance, callback_data="add_distance"
        ),
        types.InlineKeyboardButton(
            text=mt.btn_finish_training,
            callback_data="finish_training",
        ),
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)


def skip_and_cancel_keyboard():
    """Клавіатура для вибору дистанції або завершення."""
    builder = ReplyKeyboardBuilder()
    builder.add(
        types.KeyboardButton(text=mt.btn_cancel),
        types.KeyboardButton(text=mt.btn_skip),
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)

def cancel_keyboard():
    """Клавіатура "Відмінити"."""
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text=mt.btn_cancel))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)
