from aiogram.utils.markdown import text, hbold, hlink


# Константи для повторюваних елементів
DOUBLE_TAB = "\t\t"

msg_handle_start = text(
    hbold("📢 Привіт, {name}!"),
    DOUBLE_TAB + (
        "Ми помітили, що у твоєму профілі учасника бігового клубу не заповнені всі дані.\n"
        "Щоб ми могли краще організовувати тренування та заходи, будь ласка, доповни свій профіль.\n"
        "Це займе всього кілька хвилин! 😊"
    ),
    hbold("Для отримання додаткової інформації:"),
    "натисніть на кнопку "
    + hlink("тут", "tg://resolve?domain=@BaseSMLbot&start=urlpay"),
    sep="\n\n",
)
