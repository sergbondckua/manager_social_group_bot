import random
from aiogram import Router
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command

from robot.models import QuizQuestion
from common.utils import clean_tag_message
from core.settings import DEFAULT_CHAT_ID
from robot.tgbot.filters.admin import AdminFilter

admin_router = Router()
admin_router.message.filter(AdminFilter())


# Обробник команди "/start"
@admin_router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply(f"Вітаю адміне, {message.from_user.first_name}!")


# Обробник команди "/quiz"
@admin_router.message(Command("quiz"))
async def cmd_quiz(message: Message):
    question = await QuizQuestion.objects.filter(is_active=True).afirst()

    # Перевірка наявності активного запитання
    if not question:
        await message.answer("Наразі немає активних запитань.")
        return

    answers = [answer async for answer in question.answers.all()]

    # Перевірка кількості відповідей
    if len(answers) < 2:
        await message.answer("У цього запитання недостатньо відповідей.")
        return

    # Перемішування відповідей
    random.shuffle(answers)

    # Знаходження правильної відповіді
    correct_answer = next((a for a in answers if a.is_correct), None)
    if not correct_answer:
        await message.answer("У цього запитання немає правильної відповіді.")
        return

    correct_option_id = answers.index(correct_answer)
    options = [a.text for a in answers]

    # Обробка тексту запитання та пояснення
    question_text = clean_tag_message(question.text)
    explanation = (
        clean_tag_message(question.explanation)
        if question.explanation
        else None
    )

    # Відправлення зображення, якщо воно є
    if image := question.image:
        try:
            await message.bot.send_chat_action(
                chat_id=DEFAULT_CHAT_ID, action="upload_photo"
            )
            await message.bot.send_photo(
                chat_id=DEFAULT_CHAT_ID,
                photo=FSInputFile(image.path),
                caption=f"{question_text}\n#quiz | #quiz{question.id}",
                protect_content=True,
            )
        except Exception as e:
            await message.answer("Не вдалося завантажити зображення.")
            return

    # Відправлення вікторини як опитування
    try:
        await message.bot.send_chat_action(
            chat_id=DEFAULT_CHAT_ID, action="typing"
        )
        await message.bot.send_poll(
            chat_id=DEFAULT_CHAT_ID,
            question=question_text,
            options=options,
            type="quiz",
            correct_option_id=correct_option_id,
            explanation=explanation,
            is_anonymous=False,
            allows_multiple_answers=False,
        )
    except Exception as e:
        await message.answer("Не вдалося відправити вікторину.")
        return

    # Оновлення статусу запитання
    question.is_active = False
    await question.asave()
