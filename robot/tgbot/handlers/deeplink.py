from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile

from common.utils import clean_tag_message
from robot.models import DeepLink

# Ініціалізація роутера
deep_link_router = Router()


@deep_link_router.message(CommandStart())
async def handle_deeplink(message: types.Message, command: types.BotCommand):
    """
    Обробка deep link за командою /start з аргументом.

    :param message: Об'єкт повідомлення від користувача.
    :param command: Об'єкт команди /start з аргументами.
    """
    deep_link_param = command.args

    # Перевірка наявності параметра в команді
    if not deep_link_param:
        await message.answer("Не вказано параметр deep link.")
        return

    # Пошук відповідного DeepLink в базі даних
    try:
        deep_link_instance = await DeepLink.objects.filter(
            command=deep_link_param
        ).afirst()
    except Exception as e:
        await message.answer("Сталася помилка при обробці запиту.")
        return

    # Якщо відповідний deep link не знайдено
    if not deep_link_instance:
        await message.answer("Deep link не знайдено або він недійсний.")
        return

    # Форматування повідомлення
    try:
        msg = clean_tag_message(deep_link_instance.text).format(
            user_id=message.from_user.id,
            full_name=message.from_user.full_name or "Користувач",
            username=message.from_user.username or "",
            today=message.date.strftime("%d.%m.%Y"),
            current_month=message.date.strftime("%B-%Y").upper(),
        )
        if image := deep_link_instance.image:
            await message.answer_photo(
                photo=FSInputFile(image.path),
                caption=msg[:1024],
                show_caption_above_media=True,
            )
        else:
            await message.answer(msg[:4096])
    except KeyError as e:
        # Обробка випадків відсутності ключів у тексті шаблону
        await message.answer("Сталася помилка у форматуванні повідомлення.")
