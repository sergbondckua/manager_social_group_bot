import uuid

import bleach

from bank.resources.bot_msg_templates import compliment_text
from common.enums import GreetingTypeChoices
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
            "br",
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
            "br": "\n",
            "&nbsp;": " ",
            "\u00a0": " ",
            "&ndash;": "-",
            "\u2013": "-",
            "&quot;": '"',
            "&rsquo;": "'",
            "&bull;": "*",
            "&mdash;": "-",
        }

    # Очищення HTML-тегів
    cleaned_text = bleach.clean(text, tags=allowed_tags, strip=True)

    # Замінюємо символи за допомогою словника
    for symbol, replacement in replace_symbols.items():
        cleaned_text = cleaned_text.replace(symbol, replacement)

    return cleaned_text


def generate_upload_filename(instance, filename: str) -> str:
    """Функція для зміни ім'я завантаженого файлу"""
    file_extension = filename.split(".")[-1]
    new_filename = f"{uuid.uuid4().hex}.{file_extension}"
    return new_filename


from django.db.models import Count
import random


def get_random_compliment() -> str:
    """Функція для отримання випадкового компліменту з бази даних."""
    count = Compliment.objects.aggregate(count=Count("id"))["count"]

    if count and count > 0:
        random_index = random.randint(0, count - 1)
        compliment = Compliment.objects.all()[random_index]
        return compliment.text
    return "Дякуємо, що ми разом! Ви чудові!"


def get_random_greeting() -> str:
    """Функція для отримання випадкового привітання з бази даних."""
    count = Greeting.objects.filter(
        event_type=GreetingTypeChoices.BIRTHDAY, is_active=True
    ).aggregate(count=Count("id"))["count"]

    if count and count > 0:
        random_index = random.randint(0, count - 1)
        greeting = Greeting.objects.filter(
            event_type=GreetingTypeChoices.BIRTHDAY, is_active=True
        )[random_index]
        return greeting.text
    return "Зі святом! Нехай цей день буде сповнений тепла, посмішок і незабутніх емоцій!"


def get_personalized_compliment_message() -> str:
    """Функція для отримання персоналізованого повідомлення з компліментом
    Функція повертає повідомлення з випадковим компліментом, взятим з бази даних.
    """

    # Отримуємо випадковий комплімент з бази даних
    compliment = clean_tag_message(get_random_compliment())

    # Формуємо повідомлення з компліментом
    return compliment_text.format(name="{name}", compliment=compliment)


def get_random_birthday_sticker() -> str:
    """Функція для отримання випадкової наліпки телеграм з тематики 'День народження'."""
    birthday_stickers = [
        "CAACAgIAAxkBAAJa3Gfb3zHCiviF9uEWZhbUJ8qD1PxBAAIBDAACtumYS0paKO5WkCg-NgQ",
        "CAACAgIAAxkBAAJa3Wfb33NFSU08r1cIDTVM7oI2wHSYAALhBQACP5XMChpOPHjFOhuHNgQ",
        "CAACAgIAAxkBAAJa3mfb39EgWcoS9jroyFRBJd1FCqenAAJeAwACusCVBVx5KsFa_kfsNgQ",
        "CAACAgIAAxkBAAJa32fb4GFej69pBqekS9LCJqjrOooWAAKnAAM7YCQU7Vl-HjapWug2BA",
        "CAACAgIAAxkBAAJa4Gfb4LDltretLnUVAAEhb6OIB5qkmAACHwADlp-MDldYXcQNhO6MNgQ",
        "CAACAgIAAxkBAAJa4Wfb4NXGE_-ahbVTj8sEmmY72GfmAAInAAP3AsgPS9klerRucBs2BA",
        "CAACAgIAAxkBAAJa4mfb4R_p5MuYFFrk5if8B7tlRqvUAAJNAANZu_wlKIGgbd0bgvc2BA",
        "CAACAgIAAxkBAAJa42fb4ZUzGTQNrIs4OhLHyllgn2PCAAIoAANZu_wl-CwR66M5Tks2BA",
        "CAACAgIAAxkBAAJa5Gfb4oqT71u_mNGXMcXALcwpHb9KAAKlAAP3AsgP7F9kIPA4jks2BA",
        "CAACAgIAAxkBAAJa5Wfb4tWerSMl919G9k5WHgJvyMs4AAIrAAN4qOYPJV9pEP5R6jo2BA",
    ]

    if not birthday_stickers:
        raise ValueError("Список наліпок порожній!")

    return random.choice(birthday_stickers)
