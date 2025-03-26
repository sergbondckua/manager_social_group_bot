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
    "📅 Будь ласка, введіть вашу дату народження у форматі DD.MM.YYYY:"
)
msg_phone: str = text("Натисніть кнопку нижче, щоб поділитися номером 📲")
msg_first_name: str = text(
    "🖌 Введіть ваше",
    hbold("ім'я"),
    " відповідно до паспортних даних:\n",
    f"{EXAMPLE_PREFIX} Руня",
)
msg_last_name: str = text(
    "🖊 Введіть ваше",
    hbold("Прізвище"),
    " відповідно до паспортних даних:\n",
    f"{EXAMPLE_PREFIX} Кросранівська",
)
msg_press_pay_button: str = text(
    "🎽 {full_name}",
    "🆔 {user_id}",
    "🔘👈 Натиснув(ла) кнопку оплати внеску",
    sep="\n",
)
