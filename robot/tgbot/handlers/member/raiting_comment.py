import logging
from aiogram import F, types, Router
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async

from profiles.models import ClubUser
from robot.tgbot.filters.member import ClubMemberFilter
from robot.tgbot.keyboards import member as kb
from robot.tgbot.states.member import TrainingCommentStates
from robot.tgbot.text import member_template as mt
from training_events.models import (
    TrainingEvent,
    TrainingRating,
    TrainingComment,
)

rating_comment_router = Router()
rating_comment_router.message.filter(ClubMemberFilter())

logger = logging.getLogger("robot")


@rating_comment_router.callback_query(F.data == "btn_close")
async def btn_close(callback: types.CallbackQuery):
    """Закриває повідомлення і видаляє клавіатуру."""
    await callback.message.delete()
    return


@rating_comment_router.callback_query(F.data.startswith("rate_training_"))
async def process_training_rating(callback: types.CallbackQuery):
    """Обробка оцінки тренування."""

    # Розбираємо callback_data rate_training_123_5
    training_id, rating = callback.data.split("_")[-2:]
    training_id = int(training_id)
    rating = int(rating)

    try:
        training = await TrainingEvent.objects.aget(id=training_id)
        participant = await ClubUser.objects.aget(
            telegram_id=callback.from_user.id
        )

        # Зберігаємо оцінку в БД
        await TrainingRating.objects.aupdate_or_create(
            training=training,
            participant=participant,
            defaults={"rating": rating},
        )

        # Повідомляємо про успішне збереження оцінки
        await callback.answer(f"Дякую за вашу оцінку: {'⭐' * rating}")

        # Оновлюємо повідомлення, відображаємо оцінку
        await callback.message.edit_text(
            text=mt.rating_confirmation_template.format(
                title=f"{training.title} - {training.location}",
                rating=f"{'⭐' * rating}",
            ),
            reply_markup=kb.add_comment_keyboard(training_id),
        )

    except TrainingEvent.DoesNotExist:
        await callback.answer("❌ Тренування не знайдено!", show_alert=True)
    except Exception as e:
        logger.error(" Помилка при збереженні оцінки: %s", e)
        await callback.answer(
            "🚫 Сталася помилка при збереженні оцінки", show_alert=True
        )
    finally:
        await callback.answer()


@rating_comment_router.callback_query(F.data.startswith("comment_training_"))
async def request_training_comment(
        callback: types.CallbackQuery, state: FSMContext
):
    """Запит коментаря до тренування."""

    training_id = int(callback.data.split("_")[-1])

    # Зберігаємо ID тренування в стані
    await state.update_data(training_id=training_id)
    # Переходимо до наступного стану
    await state.set_state(TrainingCommentStates.waiting_for_comment)

    await callback.message.edit_text(
        "📝 Будь ласка, напишіть ваш коментар про тренування:"
    )


@rating_comment_router.message(TrainingCommentStates.waiting_for_comment)
async def process_training_comment(message: types.Message, state: FSMContext):
    """Обробка коментарів до тренування."""

    if not isinstance(message.text, str):
        await message.answer("📝 Спробуйте повторити Ваш коментар текстом:")
        return

    data = await state.get_data()
    training_id = data.get("training_id")
    try:
        training = await TrainingEvent.objects.aget(id=training_id)
        participant = await ClubUser.objects.aget(
            telegram_id=message.from_user.id
        )
        user = message.from_user.full_name or message.from_user.username
        owner_id = await sync_to_async(
            lambda: training.created_by.telegram_id
        )()
        rating = await TrainingRating.objects.aget(
            training=training, participant=participant
        )

        # Зберігаємо коментар в БД
        await TrainingComment.objects.aupdate_or_create(
            training=training,
            participant=participant,
            defaults={"comment": message.text},
        )
        await message.answer(
            mt.rating_confirmation_template.format(
                title=f"{training.title} - {training.location}",
                rating=f"{'⭐' * rating.rating}",
            )
        )
        # Відправлення повідомлення організатору
        await message.bot.send_message(
            chat_id=owner_id,
            text=mt.new_comment_template.format(
                title=f"{training.title} - {training.location}",
                comment=message.text,
                participant=user,
                training_id=training.id,
                rating=f"{'⭐' * rating.rating}",
            ),
        )

    except TrainingEvent.DoesNotExist:
        await message.answer("❌ Тренування не знайдено!", show_alert=True)
        return
    except Exception as e:
        logger.error("Помилка при коментарі: %s", e, exc_info=True)
        await message.answer(
            "🚫 Сталася помилка при надсиланні коментарі", show_alert=True
        )
    await state.clear()
