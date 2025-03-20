from aiogram.utils.markdown import text, hbold, hlink

# Спільна частина для повідомлень
common_part_text = text(
    "💬 {comment}",
    f"💰 Сума: {hbold('{amount}')}",
    f"💵 Баланс: {hbold('{balance}')}",
    "〰〰〰〰〰〰〰",
    sep="\n",
)

# Повідомлення про надходження
income_text = text(
    "✅ Зараз відбулось надходження!\n",
    "📅 {dt} 🕘 {time}",
    "👤 {description}",
    "{common_part}",
    "🤑 Радійте новим надходженням! 🎉",
    sep="\n",
)

# Повідомлення про витрати
expense_text = text(
    "🔻 Щойно були витрачені кошти!\n",
    "📅 {dt} 🕘 {time}",
    "🛍 Кому: {description}",
    f"🧾 {hlink('{title}', '{url}')}",
    "{common_part}",
    "💸 Будьте уважні з витратами, але не забувайте жити на повну! 😉",
    sep="\n",
)

# Повідомлення про внесок
payer_text = text(
    "✅ Ваш внесок отримано!\n",
    "📅 {dt} 🕘 {time}",
    "👤 {description}",
    f"🧾 {hlink('{title}', '{url}')}",
    f"💰 Сума: {hbold('{amount}')}",
    "〰〰〰〰〰〰〰",
    "🏃‍♂️ Дякуємо, що біжите разом із нами! 💖",
    sep="\n",
)

# Комплімент
compliment_text = text(
    f"📸 Шаленію від тебе, {hbold('{name}')} і вдячна тобі:",
    "🟡  🟢  🔴  🟣  🔵",
    "➖ {compliment}",
    sep="\n\n",
)
