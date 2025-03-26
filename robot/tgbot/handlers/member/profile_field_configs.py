from datetime import datetime

from django.utils import timezone

import robot.tgbot.text.member_template as mt
from robot.tgbot.keyboards.member import cancel_keyboard, contact_keyboard

# ================= КОНФІГУРАЦІЯ ПОЛІВ =================
# Кожне поле містить усі необхідні налаштування для обробки
field_configs = [
    {
        "name": "first_name",  # Назва поля в моделі ClubUser
        "request_text": mt.msg_first_name,  # Текст запиту для користувача
        "keyboard": cancel_keyboard,  # Функція для створення клавіатури
        "validation": lambda msg: 18 >= len(msg.text.strip()) > 3,  # Валідація
        "processor": lambda msg: msg.text.strip().capitalize(),  # Обробка значення
        "error_text": "❗ Ім'я повинно містити від 3 до 18 символів",  # Текст помилки
    },
    {
        "name": "last_name",
        "request_text": mt.msg_last_name,
        "keyboard": cancel_keyboard,
        "validation": lambda msg: 18 >= len(msg.text.strip()) > 3,
        "processor": lambda msg: msg.text.strip().capitalize(),
        "error_text": "❗ Прізвище повинно містити від 3 до 18 символів",
    },
    {
        "name": "phone_number",
        "request_text": mt.msg_phone,
        "keyboard": contact_keyboard,
        "validation": lambda msg: (
            msg.contact is not None and msg.contact.user_id == msg.from_user.id
        ),
        "processor": lambda msg: f"+{msg.contact.phone_number.lstrip('+')}",
        "error_text": "Хибні дані. Будь ласка, скористайтесь кнопкою знизу 👇",
    },
    {
        "name": "data_of_birth",
        "request_text": mt.msg_dob,
        "keyboard": cancel_keyboard,
        "validation": lambda msg: validate_dob(
            msg.text.strip().replace(",", ".")
        ),
        "processor": lambda msg: datetime.strptime(
            msg.text.strip().replace(",", "."), "%d.%m.%Y"
        ).date(),
        "error_text": "❗ Невірний формат або дата у майбутньому. Використовуйте DD.MM.YYYY",
    },
]


def validate_dob(text: str) -> bool:
    """Валідація дати народження.
    Перевіряє:
    - Коректність формату DD.MM.YYYY
    - Дата не може бути у майбутньому
    """
    try:
        dob = datetime.strptime(text, "%d.%m.%Y").date()
        return dob < timezone.now().date()
    except ValueError:
        return False
