from aiogram import F, types

from robot.tgbot.handlers.member.start import member_router
from robot.tgbot.filters.member import ClubMemberFilter


member_router.message.filter(ClubMemberFilter())


# Обробка оцінки тренування
@member_router.callback_query(F.data.startswith("rate_training_"))
async def process_training_rating(callback: types.CallbackQuery):
    """Обробка оцінки тренування."""

    # Розбираємо callback_data
    _, training_id, rating = callback.data.split("_")
    training_id = int(training_id)
    rating = int(rating)
