from datetime import datetime

from aiogram import types, Router
from aiogram.fsm.context import FSMContext

from profiles.models import ClubUser
from robot.tgbot.keyboards.member import contact_keyboard, cancel_keyboard
from robot.tgbot.services.member_service import update_user_field
from robot.tgbot.states.member import ProfileStates
import robot.tgbot.text.member_template as mt

profile_router = Router()


# Обробник підтвердження
@profile_router.message(lambda message: message.text == mt.btn_yes)
async def handle_yes(message: types.Message, state: FSMContext):
    """Обробляє підтвердження даних користувача."""

    user = await ClubUser.objects.aget(telegram_id=message.from_user.id)
    required_fields = []

    if not user.data_of_birth:
        required_fields.append("dob")
    if not user.phone_number:
        required_fields.append("phone")

    await state.update_data(required_fields=required_fields)

    if "phone" in required_fields:
        await message.answer(
            mt.msg_phone,
            reply_markup=contact_keyboard(),
        )
        await state.set_state(ProfileStates.waiting_for_phone)
    elif "dob" in required_fields:
        await message.answer(mt.msg_dob, reply_markup=cancel_keyboard())
        await state.set_state(ProfileStates.waiting_for_dob)
    else:
        await state.clear()


# Обробник відмови
@profile_router.message(lambda message: message.text == mt.btn_no)
async def handle_no(message: types.Message):
    await message.answer(
        "❌ Ви можете заповнити дані пізніше через особистий кабінет.",
        reply_markup=types.ReplyKeyboardRemove(),
    )


# Обробник скасувати
@profile_router.message(lambda message: message.text == mt.btn_cancel)
async def handle_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Шкода, що Ви передумали.",
        reply_markup=types.ReplyKeyboardRemove(),
    )


# Обробник телефону
@profile_router.message(ProfileStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):

    if not message.contact:
        await message.answer("Будь ласка, скористайтесь кнопкою знизу 👇")
        return

    if message.contact.user_id != message.from_user.id:
        await message.answer(
            "❗ Цей номер не є вашим, все ж таки скористайтесь кнопкою знизу 👇"
        )
        return

    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = f"+{phone}"

    user = await ClubUser.objects.aget(telegram_id=message.from_user.id)
    await update_user_field(user, "phone_number", phone)

    data = await state.get_data()
    required_fields = data.get("required_fields", []).copy()
    required_fields.remove("phone")

    if required_fields:
        await state.update_data(required_fields=required_fields)
        await message.answer(mt.msg_dob, reply_markup=cancel_keyboard())
        await state.set_state(ProfileStates.waiting_for_dob)
    else:
        await message.answer(
            "✅ Дані успішно оновлено!",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        await state.clear()


# Обробник дати народження
@profile_router.message(ProfileStates.waiting_for_dob)
async def process_dob(message: types.Message, state: FSMContext):
    user = await ClubUser.objects.aget(telegram_id=message.from_user.id)
    try:
        dob = datetime.strptime(message.text, "%d.%m.%Y").date()
        await update_user_field(user, "data_of_birth", dob)
    except ValueError:
        await message.answer(
            "❗ Невірний формат дати. Використовуйте DD.MM.YYYY (наприклад 31.12.2000)"
        )
        return

    await update_user_field(user, "data_of_birth", dob)
    data = await state.get_data()
    required_fields = data.get("required_fields", []).copy()
    required_fields.remove("dob")

    if not required_fields:
        await message.answer(
            "✅ Дані успішно оновлено!",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        await state.clear()
