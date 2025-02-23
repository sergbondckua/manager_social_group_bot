import bleach
import uuid


def clean_tag_message(text: str) -> str:
    """
    Видаляє всі HTML-теги, крім дозволених.

    :param text: Вхідний HTML-текст.
    :return: Очищений текст.
    """
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
    cleaned_text = bleach.clean(text, tags=allowed_tags, strip=True)
    # Замінюємо `&nbsp;` та його Unicode-еквівалент на звичайний пробіл
    cleaned_text = cleaned_text.replace("&nbsp;", " ").replace("\u00a0", " ")
    return cleaned_text


def generate_upload_filename(instance, filename):
    """ Функція для зміни ім'я завантаженого файлу """

    file_extension = filename.split(".")[-1]
    new_filename = f"{uuid.uuid4().hex}.{file_extension}"
    return new_filename
