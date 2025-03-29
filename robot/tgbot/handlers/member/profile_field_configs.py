import re
from datetime import datetime

from aiogram import types
from django.utils import timezone

import robot.tgbot.text.member_template as mt
from robot.tgbot.keyboards.member import cancel_keyboard, contact_keyboard


# КОНСТАНТИ ТА ТИПИ

NAME_MIN_LEN = 3
NAME_MAX_LEN = 18
MIN_AGE = 12  # Мінімальний вік користувача
NAME_PATTERN = re.compile(r"^[a-zA-Zа-яА-ЯєЄїЇіІґҐ'’\-]+$")

# КОНФІГУРАЦІЯ ПОЛІВ

field_configs = [
    {
        "name": "first_name",  # Назва поля в моделі ClubUser
        "request_text": mt.msg_first_name,  # Текст запиту для користувача
        "keyboard": "cancel_keyboard",  # Функція для створення клавіатури
        "validation": "validate_first_name",  # Валідація
        "processor": "process_first_name",  # Обробка значення
        "error_text": mt.msg_first_name_error.format(
            name_min_len=NAME_MIN_LEN, name_max_len=NAME_MAX_LEN
        ),  # Текст помилки
    },
    {
        "name": "last_name",
        "request_text": mt.msg_last_name,
        "keyboard": "cancel_keyboard",
        "validation": "validate_last_name",
        "processor": "process_last_name",
        "error_text": mt.msg_last_name_error.format(
            name_min_len=NAME_MIN_LEN, name_max_len=NAME_MAX_LEN
        ),
    },
    {
        "name": "phone_number",
        "request_text": mt.msg_phone,
        "keyboard": "contact_keyboard",
        "validation": "validate_phone",
        "processor": "process_phone",
        "error_text": mt.msg_phone_error,
    },
    {
        "name": "data_of_birth",
        "request_text": mt.msg_dob,
        "keyboard": "cancel_keyboard",
        "validation": "validate_dob",
        "processor": "process_dob",
        "error_text": mt.msg_dob_error.format(min_age=MIN_AGE),
    },
]


# ВАЛІДАЦІЯ ПОЛІВ

def validate_name(msg: types.Message) -> bool:
    """Універсальна валідація для імені та прізвища"""
    text = msg.text.strip()
    return (
        NAME_MIN_LEN <= len(text) <= NAME_MAX_LEN
        and NAME_PATTERN.fullmatch(text) is not None
    )


def validate_phone(msg: types.Message) -> bool:
    """Валідація телефону користувача"""
    return msg.contact is not None and msg.contact.user_id == msg.from_user.id


def validate_dob(msg: types.Message) -> bool:
    """Валідація дати народження з перевіркою віку"""
    try:
        # Нормалізація перед перевіркою
        normalized_date = msg.text.strip().replace(",", ".").replace("/", ".")
        dob = datetime.strptime(normalized_date, "%d.%m.%Y").date()
        today = timezone.now().date()
        age = (
            today.year
            - dob.year
            - ((today.month, today.day) < (dob.month, dob.day))
        )
        return dob < today and age >= MIN_AGE
    except ValueError:
        return False


# ОБРОБКА ПОЛІВ

def process_first_name(msg: types.Message):
    """Обробка імені користувача"""
    return msg.text.strip().title()


def process_last_name(msg: types.Message):
    """Обробка прізвища користувача"""
    return msg.text.strip().title()


def process_phone(msg: types.Message):
    """Обробка телефону користувача"""
    return f"+{msg.contact.phone_number.lstrip('+')}"


def process_dob(msg: types.Message):
    """Парсинг дати з автоматичним виправленням роздільників"""
    return datetime.strptime(
        msg.text.strip().replace(",", ".").replace("/", "."), "%d.%m.%Y"
    ).date()


# РЕЄСТРАЦІЯ ФУНКЦІЙ ДЛЯ ПОЛІВ

# Конфігурація клавіатур для полів
keyboard_factories = {
    "cancel_keyboard": cancel_keyboard,
    "contact_keyboard": contact_keyboard,
}
# Конфігурація валідацій
validation_functions = {
    "validate_first_name": validate_name,
    "validate_last_name": validate_name,
    "validate_phone": validate_phone,
    "validate_dob": validate_dob,
}
# Конфігурація обробників
processor_functions = {
    "process_first_name": process_first_name,
    "process_last_name": process_last_name,
    "process_phone": process_phone,
    "process_dob": process_dob,
}
