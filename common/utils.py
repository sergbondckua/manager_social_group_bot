import random
import uuid

import bleach

from bank.resources.bot_msg_templates import compliment_text
from common.models import Compliment, Greeting


def clean_tag_message(
    text: str, allowed_tags=None, replace_symbols=None
) -> str:
    """
    Видаляє всі HTML-теги, крім дозволених, та очищає певні символи.

    :param text: Вхідний HTML-текст.
    :param allowed_tags: Список дозволених HTML-тегів.
    :param replace_symbols: Словник для заміни символів. Ключ - символ для заміни, значення - на що заміняти.
    :return: Очищений текст.
    """
    # За замовчуванням дозволяються певні теги
    if allowed_tags is None:
        allowed_tags = [
            "b",
            "strong",
            "i",
            "em",
            "u",
            "ins",
            "s",
            "strike",
            "a",
            "code",
            "pre",
        ]

    # За замовчуванням замінюємо певні символи
    if replace_symbols is None:
        replace_symbols = {
            "&nbsp;": " ",
            "\u00a0": " ",
            "&ndash;": "-",
            "\u2013": "-",
            "&quot;": '"',
        }

    # Очищення HTML-тегів
    cleaned_text = bleach.clean(text, tags=allowed_tags, strip=True)

    # Замінюємо символи за допомогою словника
    for symbol, replacement in replace_symbols.items():
        cleaned_text = cleaned_text.replace(symbol, replacement)

    return cleaned_text


def generate_upload_filename(instance, filename):
    """Функція для зміни ім'я завантаженого файлу"""

    file_extension = filename.split(".")[-1]
    new_filename = f"{uuid.uuid4().hex}.{file_extension}"
    return new_filename


def get_random_compliment():
    """Функція для отримання випадкового комплементу з бази даних"""

    compliments = Compliment.objects.all()
    if compliments.exists():
        return random.choice(compliments).text
    return "Дякуємо, що ми разом! Ви чудові!"  # Значення за замовчуванням


def get_random_greeting() -> str:
    """Функція для отримання випадкового привітання з бази даних."""

    # Отримуємо всі привітання з бази даних
    greetings = Greeting.objects.all()

    # Якщо є привітання, то повертаємо випадкове
    if greetings.exists():
        return random.choice(greetings).text

    # Якщо немає привітань, то повертаємо за замовчуванням
    return "Зі святом! Нехай цей день буде сповнений тепла, посмішок і незабутніх емоцій!"


def get_personalized_compliment_message() -> str:
    """Функція для отримання персоналізованого повідомлення з компліментом
    Функція повертає повідомлення з випадковим компліментом, взятим з бази даних.
    """

    # Отримуємо випадковий комплімент з бази даних
    compliment = clean_tag_message(get_random_compliment())

    # Формуємо повідомлення з компліментом
    return compliment_text.format(name="{name}", compliment=compliment)
