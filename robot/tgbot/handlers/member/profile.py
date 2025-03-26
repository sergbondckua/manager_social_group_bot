import logging

from aiogram import types, Router
from aiogram.fsm.context import FSMContext

from robot.tgbot.handlers.member.profile_field_configs import field_configs
from robot.tgbot.services.member_service import update_user_field, get_user_or_error, get_required_fields
from robot.tgbot.states.member import ProfileStates
import robot.tgbot.text.member_template as mt

logger = logging.getLogger("robot")
profile_router = Router()

# ================= ОБРОБНИКИ ПОВІДОМЛЕНЬ =================


# Обробник погодження на заповнення профілю
@profile_router.message(lambda message: message.text == mt.btn_yes)
async def handle_yes(message: types.Message, state: FSMContext):
    """Початок процесу заповнення профілю"""
    user = await get_user_or_error(message.from_user.id, message)
    if not user:
        return

    # Отримуємо список полів, які потрібно заповнити
    required_fields = await get_required_fields(user, field_configs)

    if not required_fields:
        await message.answer(
            "ℹ️ Всі дані вже заповнені!",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        await state.clear()
        return

    # Зберігаємо стан та запускаємо процес заповнення
    await state.set_data({"required_fields": required_fields})
    await process_next_field(message, state)


async def process_next_field(message: types.Message, state: FSMContext):
    """Обробляє перехід між полями для заповнення"""
    data = await state.get_data()
    required_fields = data.get("required_fields", [])

    if not required_fields:
        # Усі поля заповнені - завершуємо процес
        await message.answer(
            "✅ Всі дані успішно оновлені! Дякую!",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        await state.clear()
        return

    # Беремо перше поле зі списку та формуємо запит
    current_field = required_fields[0]
    await message.answer(
        current_field["request_text"],
        reply_markup=current_field[
            "keyboard"
        ](),  # Викликаємо функцію створення клавіатури
    )
    await state.set_state(ProfileStates.waiting_field_input)


@profile_router.message(ProfileStates.waiting_field_input)
async def process_field_input(message: types.Message, state: FSMContext):
    """Універсальний обробник для всіх полів"""

    # Спочатку перевіряємо скасування
    if message.text == mt.btn_cancel:
        await handle_cancel(message, state)
        return

    data = await state.get_data()
    required_fields = data.get("required_fields", [])

    if not required_fields:
        await state.clear()
        return

    current_field = required_fields[0]

    # === ВАЛІДАЦІЯ ДАНИХ ===
    if not current_field["validation"](message):
        await message.answer(current_field["error_text"])
        return

    # === ОБРОБКА ЗНАЧЕННЯ ===
    try:
        processed_value = current_field["processor"](message)
    except Exception as e:
        logger.error("Помилка обробки поля %s: %s", current_field["name"], e)
        await message.answer("❌ Помилка обробки даних")
        return

    # === ОНОВЛЕННЯ БАЗИ ДАНИХ ===
    user = await get_user_or_error(message.from_user.id, message)
    if not user:
        await state.clear()
        return

    try:
        await update_user_field(user, current_field["name"], processed_value)
    except Exception as e:
        logger.error("Помилка оновлення поля %s: %s", current_field["name"], e)
        await message.answer("❌ Помилка збереження даних")
        return

    # === ПЕРЕХІД ДО НАСТУПНОГО ПОЛЯ ===

    # Видаляємо оброблене поле зі списку
    remaining_fields = required_fields[1:]

    # Оновлюємо список полів
    await state.update_data(required_fields=remaining_fields)

    # Рекурсивний виклик для наступного поля
    await process_next_field(message, state)


# ================= ДОДАТКОВІ ОБРОБНИКИ =================


# Обробник відмови
@profile_router.message(lambda message: message.text == mt.btn_no)
async def handle_no(message: types.Message):
    """Обробник відмови заповнювати дані"""
    await message.answer(
        "❌ Ви можете заповнити дані пізніше через особистий кабінет.",
        reply_markup=types.ReplyKeyboardRemove(),
    )


# Обробник скасування
@profile_router.message(lambda message: message.text == mt.btn_cancel)
async def handle_cancel(message: types.Message, state: FSMContext):
    """Обробник скасування процесу"""

    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer(
        "Шкода, що Ви передумали.",
        reply_markup=types.ReplyKeyboardRemove(),
    )


# ================= ПРИКЛАД ДОДАВАННЯ НОВОГО ПОЛЯ =================
# Для додавання нового поля додайте конфігурацію в FIELD_CONFIGS:
#
# {
#     'name': 'email',
#     'request_text': "📧 Введіть ваш email:",
#     'keyboard': cancel_keyboard,
#     'validation': lambda msg: '@' in msg.text and '.' in msg.text.split('@')[-1],
#     'processor': lambda msg: msg.text.strip().lower(),
#     'error_text': "❗ Невірний формат email"
# }
