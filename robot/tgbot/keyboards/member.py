from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram import types
from robot.tgbot.text import member_template as mt


def yes_no_keyboard():
    """Клавіатура "Так/Ні"."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text=mt.btn_yes),
        types.KeyboardButton(text=mt.btn_no),
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)


def contact_keyboard():
    """Клавіатура "Поділитися номером"."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(
            text="📱 Поділитися номером", request_contact=True
        ),
        types.KeyboardButton(text=mt.btn_cancel),
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)


def cancel_keyboard():
    """Клавіатура "Відмінити"."""
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text=mt.btn_cancel))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)


def rating_keyboard(training_id):
    """Інлайн-клавіатура для оцінки тренування."""
    builder = InlineKeyboardBuilder()
    buttons = [
        InlineKeyboardButton(
            text=f"{'⭐' * i}",
            callback_data=f"rate_training_{training_id}_{i}",
        )
        for i in range(1, 6)
    ]
    builder.add(
        *buttons,
        InlineKeyboardButton(
            text=mt.btn_close,
            callback_data="btn_close",
        ),
    )
    builder.adjust(3, 2, 1)
    return builder.as_markup()


def add_comment_keyboard(training_id):
    """Інлайн-клавіатура для додавання коментаря."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="📝 Залишити коментар",
            callback_data=f"comment_training_{training_id}",
        ),
        InlineKeyboardButton(text=mt.btn_close, callback_data="btn_close"),
    )
    return builder.as_markup()
