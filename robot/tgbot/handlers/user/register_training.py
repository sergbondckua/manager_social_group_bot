import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from asgiref.sync import sync_to_async
from django.utils import timezone

from profiles.models import ClubUser
from robot.tgbot.keyboards import user as kb
from training_events.models import (
    TrainingEvent,
    TrainingRegistration,
    TrainingDistance,
)

reg_training_router = Router()

# Налаштування логування
logger = logging.getLogger("robot")


@reg_training_router.callback_query(F.data == "btn_close")
async def btn_close(callback: types.CallbackQuery):
    """Закриває повідомлення і видаляє клавіатуру."""
    await callback.message.delete()
    return


async def get_username(comeback: types.CallbackQuery | types.Message):
    """Повертає ім'я користувача"""
    username = (
        f"@{comeback.from_user.username}"
        if comeback.from_user.username
        else ""
    )
    return username


async def get_full_name(
    comeback: types.CallbackQuery | types.Message, participant: ClubUser
):
    """Повертає повне ім'я користувача"""
    if not participant.first_name or not participant.last_name:
        return comeback.from_user.full_name
    else:
        return f"{participant.first_name} {participant.last_name}"


async def send_creator_training_notification(
    training: TrainingEvent, message: types.Message, text: str
):
    """
    Надсилає повідомлення організатору тренування.

    Args:
        training (TrainingEvent): Подія тренування.
        message (types.Message): Повідомлення від бота.
        text (str): Текст повідомлення.
    """
    owner_id = await sync_to_async(lambda: training.created_by.telegram_id)()
    logger.info("Надсилаємо повідомлення організатору %s", owner_id)

    await message.bot.send_message(
        chat_id=owner_id,
        text=text,
    )


@reg_training_router.callback_query(F.data.startswith("register_training_"))
async def register_training(callback: types.CallbackQuery):
    """Реєстрація на тренування"""
    user_id = callback.from_user.id
    user_full_name = callback.from_user.full_name
    training_id = int(callback.data.split("_")[-1])

    try:
        training = await TrainingEvent.objects.select_related().aget(
            id=training_id
        )
        participant = await ClubUser.objects.aget(telegram_id=user_id)
    except (TrainingEvent.DoesNotExist, ClubUser.DoesNotExist):
        await callback.message.bot.send_message(
            chat_id=user_id,
            text="❌ Тренування або профіль користувача не знайдено!",
        )
        return

    # Перевіряємо чи тренування було скасовано
    if training.is_cancelled:
        await callback.answer(
            text="⚠️ Тренування було скасовано!",
            show_alert=True,
        )
        return

    # Перевіряємо чи тренування пройшло
    if training.date < timezone.now():
        await callback.answer(
            text="⚠️ Це тренування вже відбулося!",
            show_alert=True,
        )
        return

    # Перевіряємо, чи користувач вже зареєстрований
    existing_registration = await TrainingRegistration.objects.filter(
        training=training, participant=participant
    ).aexists()
    if existing_registration:
        await callback.answer(
            text="⚠️ Ви вже зареєстровані на це тренування!",
            show_alert=True,
        )
        return

    # Якщо тренування має більше однієї дистанції
    if await training.distances.acount() > 1:
        distances = []
        async for d in training.distances.all():
            distances.append(
                {
                    "distance": d.distance,
                    "training_id": training_id,
                    "distance_id": d.id,
                }
            )

        await callback.message.bot.send_message(
            chat_id=user_id,
            text=f"🏃‍♀️ Тренування: {training.title}\n"
            f"📅 Дата: {training.date.strftime('%d.%m.%Y %H:%M')}\n"
            f"📍 Місце: {training.location}\n\n"
            "Оберіть дистанцію на яку бажаєте зареєструватися:",
            reply_markup=kb.distance_keyboard(distances),
        )
        return

    # Якщо тільки одна дистанція - реєструємо відразу
    distance: TrainingDistance = await training.distances.afirst()

    # Перевіряємо максимальну кількість учасників
    if distance.max_participants != 0:
        if await training.registrations.acount() >= distance.max_participants:
            await callback.answer(
                text="⚠️ Вибачте, максимальна кількість учасників вже зареєстрована!",
                show_alert=True,
            )
            return

    # Створюємо реєстрацію
    registration = await TrainingRegistration.objects.acreate(
        training=training, participant=participant, distance=distance
    )

    logger.info(
        "Користувач %s (ID: %s) зареєстрований на тренування %s",
        user_full_name or "",
        user_id,
        training.title,
    )

    await callback.message.bot.send_message(
        chat_id=user_id,
        text=f"✅ Реєстрація успішна!\n\n"
        f"👤 Учасник: {await get_full_name(callback, participant)}\n"
        f"🏃‍♀️ Тренування: {training.title}\n"
        f"📅 Дата: {training.date.strftime('%d.%m.%Y %H:%M')}\n"
        f"📍 Місце: {training.location}\n"
        f"🎯 Дистанція: {distance.distance} км\n"
        f"🔗 Всі реєстрації: /my_trainings\n\n"
        "Бажаємо успішного тренування! 💪",
    )

    # Надсилаємо повідомлення організатору про реєстрацію учасника
    msg = (
        f"🆕 Нова реєстрація на тренування!\n\n"
        f"👤 Учасник: {await get_full_name(callback, participant)} {await get_username(callback)}\n"
        f"🏃‍♀️ Тренування: {training.title}\n"
        f"📅 Дата: {training.date.strftime('%d.%m.%Y %H:%M')}\n"
        f"📍 Місце: {training.location}\n"
        f"🎯 Дистанція: {distance.distance} км"
    )
    await send_creator_training_notification(training, callback.message, msg)


@reg_training_router.callback_query(F.data.startswith("distance_"))
async def register_for_distance(callback: types.CallbackQuery):
    """Реєстрація на конкретну дистанцію"""
    user_id = callback.from_user.id
    user_full_name = callback.from_user.full_name

    # Парсимо дані з callback_data: distance_123_1
    training_id, distance_id = callback.data.split("_")[-2:]

    try:
        training = await TrainingEvent.objects.aget(id=training_id)
        distance = await training.distances.aget(id=distance_id)
        participant = await ClubUser.objects.aget(telegram_id=user_id)
    except (TrainingEvent.DoesNotExist, ClubUser.DoesNotExist):
        await callback.message.bot.send_message(
            chat_id=user_id,
            text="❌ Тренування, дистанція або профіль не знайдено!",
        )
        return

    # Перевіряємо чи тренування пройшло
    if training.date < timezone.now():
        await callback.answer(
            text="⚠️ Це тренування вже відбулося!",
            show_alert=True,
        )
        return

    # Перевіряємо чи тренування було скасовано
    if training.is_cancelled:
        await callback.answer(
            text="⚠️ Тренування було скасовано!",
            show_alert=True,
        )
        return

    # Перевіряємо кількість учасників
    if distance.max_participants != 0:
        if await training.registrations.acount() >= distance.max_participants:
            await callback.answer(
                text="⚠️ Вибачте, максимальна кількість учасників на цю дистанцію вже зареєстрована!",
                show_alert=True,
            )
            return

    # Перевіряємо повторну реєстрацію
    existing_registration = await TrainingRegistration.objects.filter(
        training=training, participant=participant
    ).aexists()
    if existing_registration:
        await callback.answer(
            text="⚠️ Ви вже зареєстровані на це тренування!",
            show_alert=True,
        )
        return

    # Створюємо реєстрацію
    await TrainingRegistration.objects.acreate(
        training=training, participant=participant, distance=distance
    )

    logger.info(
        "Користувач %s (ID: %s) зареєстрований на тренування %s, дистанція %s km",
        user_full_name or "",
        user_id,
        training.title,
        distance.distance,
    )

    # Видаляємо попереднє повідомлення з вибором дистанції
    await callback.message.delete()

    await callback.message.bot.send_message(
        chat_id=user_id,
        text=f"✅ Реєстрація успішна!\n\n"
        f"👤 Учасник: {await get_full_name(callback, participant)}\n"
        f"🏃‍♀️ Тренування: {training.title}\n"
        f"📅 Дата: {training.date.strftime('%d.%m.%Y %H:%M')}\n"
        f"📍 Місце: {training.location}\n"
        f"🎯 Дистанція: {distance.distance} км\n"
        f"🔗 Всі реєстрації: /my_trainings\n\n"
        "Бажаємо успішного тренування! 💪",
    )

    # Відправляємо повідомлення адміністраторам про реєстрацію
    msg = (
        f"🆕 Нова реєстрація на тренування!\n\n"
        f"👤 Учасник: {await get_full_name(callback, participant)} {await get_username(callback)}\n"
        f"🏃‍♀️ Тренування: {training.title}\n"
        f"📅 Дата: {training.date.strftime('%d.%m.%Y %H:%M')}\n"
        f"📍 Місце: {training.location}\n"
        f"🎯 Дистанція: {distance.distance} км"
    )
    await send_creator_training_notification(training, callback.message, msg)


@reg_training_router.message(F.text.startswith("/unregister_training_"))
async def unregister_training(message: types.Message):
    """Відміна реєстрації на тренування"""
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name
    training_id = int(message.text.split("_")[-1])

    try:
        training = await TrainingEvent.objects.aget(id=training_id)
        participant = await ClubUser.objects.aget(telegram_id=user_id)
    except (TrainingEvent.DoesNotExist, ClubUser.DoesNotExist):
        await message.bot.send_message(
            chat_id=user_id,
            text="❌ Тренування або профіль не знайдено!",
        )
        return

    # Шукаємо реєстрацію
    try:
        registration = await TrainingRegistration.objects.aget(
            training=training, participant=participant
        )
        await registration.adelete()

        logger.info(
            "Користувач %s (ID: %s) скасував реєстрацію на тренування %s",
            user_full_name or "",
            user_id,
            training.title,
        )

        await message.bot.send_message(
            chat_id=user_id,
            text=f"❌ Реєстрацію скасовано\n\n"
            f"🏃‍♀️ Тренування: {training.title}\n"
            f"📅 Дата: {training.date.strftime('%d.%m.%Y %H:%M')}\n\n"
            "Ви більше не зареєстровані на це тренування.",
        )

        # Відправляємо повідомлення адміністраторам про скасовану реєстрацію
        msg = (
            f"❌ Учасник скасував реєстрацію!\n\n"
            f"🏃‍♀️ Тренування: {training.title}\n"
            f"📅 Дата: {training.date.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"👤 Учасник: {await get_full_name(message, participant)} {await get_username(message)}\n"
        )
        await send_creator_training_notification(training, message, msg)

    except TrainingRegistration.DoesNotExist:
        await message.bot.send_message(
            chat_id=user_id,
            text="⚠️ Ви не були зареєстровані на це тренування!",
        )


# @reg_training_router.callback_query(F.data == "my_registrations")
@reg_training_router.message(Command("my_trainings"))
async def show_my_registrations(message: types.Message):
    """Показує список реєстрацій користувача"""
    user_id = message.from_user.id

    try:
        participant = await ClubUser.objects.aget(telegram_id=user_id)
    except ClubUser.DoesNotExist:
        await message.bot.send_message(
            chat_id=user_id,
            text="❌ Профіль користувача не знайдено!",
        )
        return

    # Отримуємо активні реєстрації
    registrations = []
    async for reg in TrainingRegistration.objects.select_related(
        "training", "distance"
    ).filter(participant=participant, training__date__gte=timezone.now()):
        registrations.append(reg)

    if not registrations:
        await message.bot.send_message(
            chat_id=user_id,
            text="📋 У вас немає активних реєстрацій на тренування.",
        )
        return

    text = "📋 Ваші реєстрації:\n\n"
    for reg in registrations:
        text += (
            f"🏃‍♀️ {reg.training.title}\n"
            f"📅 {reg.training.date.strftime('%d.%m.%Y %H:%M')}\n"
            f"📍 {reg.training.location}\n"
            f"🎯 {reg.distance.distance} км\n"
            f"📝 Зареєстровано: {reg.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"🚫 Відмінити реєстрацію: /unregister_training_{reg.training.id}\n"
            "--------------------------------\n\n"
        )

    await message.bot.send_message(
        chat_id=user_id,
        text=text,
    )
