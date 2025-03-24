from datetime import datetime

from django.utils import timezone

import robot.tgbot.text.member_template as mt
from robot.tgbot.keyboards.member import cancel_keyboard, contact_keyboard

# ================= КОНФІГУРАЦІЯ ПОЛІВ =================
# Кожне поле містить усі необхідні налаштування для обробки
field_configs = [
    {
        "name": "phone_number",  # Назва поля в моделі ClubUser
        "request_text": mt.msg_phone,  # Текст запиту для користувача
        "keyboard": contact_keyboard,  # Функція для створення клавіатури
        "validation": lambda msg: (
            msg.contact is not None and msg.contact.user_id == msg.from_user.id
        ),  # Валідація
        "processor": lambda msg: f"+{msg.contact.phone_number.lstrip('+')}",  # Обробка значення
        "error_text": "Хибні дані. Будь ласка, скористайтесь кнопкою знизу 👇",  # Текст помилки
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
