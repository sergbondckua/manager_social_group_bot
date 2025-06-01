from aiogram.utils.markdown import text, hbold, hcode, hitalic, hlink

msg_my_id: str = text(
    "Ваша інформація:\n",
    hbold("🚻 ПІБ:") + " {full_name}",
    hbold("🪪 Username:") + hcode(" {username}"),
    hbold("🆔 Ваш ID:") + hcode(" {user_id}"),
    hbold("💬 Чат ID:") + hcode(" {chat_id}"),
    hbold("🔸 Заголовок:") + hcode(" {title}"),
    sep="\n",
)

format_my_reg_training = text(
    "🏃‍♀️ " + hbold("{title}"),
    "📅 " + hbold("{date}"),
    "📍 {location}",
    "🎯 {distance} км\n",
    "📝 Зареєстровано: " + hbold("{created_at}"),
    "🔙 Відмінити реєстрацію: /unreg_training_{training_id}",
    "--------------------------------\n",
    sep="\n",
)
format_unregister_template = text(
    hbold("‼ Учасник {username} скасував реєстрацію ‼\n"),
    "🏃‍♀️ Тренування: " + hbold("{title}"),
    "📅 Дата: " + hbold("{date}\n"),
    "👤 Учасник: " + hbold("{participant_name} {username}"),
    sep="\n",
)
format_unregister_confirmation = text(
    hbold("⚠ Реєстрацію скасовано\n"),
    "🏃‍♀️ " + hbold("Тренування: ") + hitalic("{title}"),
    "📅 " + hbold("Дата: ") + "{date}\n",
    hitalic("‼ Ви більше не зареєстровані на це тренування."),
    sep="\n",
)
format_registration_template = text(
    hbold("🆕 Нова реєстрація на тренування!\n"),
    "👤 " + hbold("Учасник: ") + "{participant} {username}",
    "🏃‍♀️ " + hbold("Тренування: ") + "{title}",
    "📅 " + hbold("Дата: ") + "{date}",
    "📍 " + hbold("Місце: ") + "{location}",
    "🎯 " + hbold("Дистанція: ") + "{distance} км",
    sep="\n",
)
format_success_registration_template = text(
    hbold("✅ Реєстрація успішна!\n"),
    "👤 " + hbold("Учасник: ") + hitalic("{participant}"),
    "🏃‍♀️ " + hbold("Тренування: ") + "{title}",
    "📅 " + hbold("Дата: ") + "{date}",
    "📍 " + hbold("Місце: ") + "{location}",
    "🎯 " + hbold("Дистанція: ") + "{distance} км\n",
    "🔗 " + hbold("Всі мої реєстрації: ") + " /my_trainings\n",
    hitalic("✨ Бажаємо успішного тренування! 💪"),
    sep="\n",
)
format_distance_selection_template = text(
    "🏃‍♀️ " + hbold("Тренування:") + " {title}\n",
    "📅 " + hbold("Дата:") + " {date}",
    "📍 " + hbold("Місце:") + " {location}\n",
    hitalic("Оберіть дистанцію на яку бажаєте зареєструватися: 👇"),
    sep="\n"
)