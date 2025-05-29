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


def create_training_publish_and_delete_keyboard(training_id: int):
    """Інлайн-клавіатура для публікації тренування."""
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text=mt.btn_training_publish,
            callback_data=f"publish_training_{training_id}",
        ),
        types.InlineKeyboardButton(
            text=mt.btn_training_delete,
            callback_data=f"delete_training_{training_id}",
        ),
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)


def confirmation_keyboard(prefix: str):
    """Інлайн-клавіатура для підтвердження."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Так", callback_data=f"{prefix}_yes")
    builder.button(text="❌ Ні, відмінити", callback_data=f"{prefix}_no")
    return builder.as_markup()

def revoke_training_keyboard(training_id: int):
    """Інлайн-клавіатура для скасування тренування."""
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text=mt.btn_cancel_training,
            callback_data=f"revoke_training_{training_id}",
        ),
        types.InlineKeyboardButton(
            text="🚫 Закрити",
            callback_data=f"revoke_training_close_{training_id}",
        )
    )
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)