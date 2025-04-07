from aiogram.utils.markdown import text, hbold, hlink

# Константи для повторюваних елементів
DOUBLE_TAB: str = "\t\t"
EXAMPLE_PREFIX: str = f"{DOUBLE_TAB}Приклад:"

# Повідомлення для стартового хендлера
msg_handle_start: str = text(
    hbold("📢 Привіт, {name}!"),
    f"{DOUBLE_TAB}Ми помітили, що у твоєму профілі учасника бігового клубу не заповнені всі дані.\n"
    "Щоб ми могли краще організовувати тренування та заходи, будь ласка, доповни свій профіль.\n"
    "Це займе всього кілька хвилин! 😊",
    hbold("Для погодження натисніть на відповідну кнопку нижче 👇"),
    sep="\n\n",
)

# Кнопки
btn_yes: str = text("👍 Так")
btn_no: str = text("👎 Ні")
btn_cancel: str = text("🚫 Скасувати")

# Інші повідомлення
msg_dob: str = text(
    "📅 Будь ласка, введіть вашу дату народження у форматі ДД.ММ.РРРР:"
)
msg_dob_error: str = text(
"❗ Невірний формат або недопустима дата.",
            "Мінімальний вік - {min_age} років.",
            "Формат: ДД.ММ.РРРР (дозволені роздільники: . , /)",
            "Приклад: 01.01.2000; 01,01,2000; 01/01/2000",
            sep="\n",
)
msg_phone: str = text("Натисніть кнопку нижче, щоб поділитися номером 📲")
msg_phone_error: str = text(
    "❗ Хибні дані або номер Вам не належить. ",
    "Будь ласка, скористайтесь кнопкою знизу 👇",
    sep="\n",
)

msg_first_name: str = text(
    "🖌 Введіть ваше",
    hbold("ім'я"),
    " відповідно до паспортних даних:\n",
    f"{EXAMPLE_PREFIX} Руня",
)
msg_first_name_error: str = text(
    "❗ Ім'я повинно містити {name_min_len}-{name_max_len} літер.",
)

msg_last_name: str = text(
    "🖊 Введіть ваше",
    hbold("Прізвище"),
    " відповідно до паспортних даних:\n",
    f"{EXAMPLE_PREFIX} Кросранівська",
)
msg_last_name_error: str = text(
    "❗ Прізвище повинно містити {name_min_len}-{name_max_len} літер."
)

msg_press_deeplink_button: str = text(
    "🎽 {full_name}",
    "🆔 {user_id}",
    f"🔘👈 Натиснув(ла) кнопку {hbold('{deep_link_text}')}",
    sep="\n",
)
