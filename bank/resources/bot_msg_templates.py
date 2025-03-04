from aiogram.utils.markdown import text, hbold, hlink


common_part_text = text(
    "💬 {comment}",
    "💰 Сума: " + hbold("{amount}"),
    "💵 Баланс: " + hbold("{balance}"),
    "〰〰〰〰〰〰〰",
    sep="\n",
)
income_text = text(
    text("✅ Зараз відбулось надходження!\n"),
    "📅 {dt} 🕘 {time}",
    "👤 {description}",
    "{common_part}",
    "🤑 Радуйтеся новим надходженням! 🎉",
    sep="\n",
)
expense_text = text(
    text("🔻 Щойно були витрачені кошти!\n"),
    "📅 {dt} 🕘 {time}",
    "🛍 Кому: {description}",
    "🧾 " + hlink("{title}", "{url}"),
    "{common_part}",
    "💸 Будьте уважні з витратами, але не забувайте жити на повну! 😉",
    sep="\n",
)
payer_text = text(
    text("✅ Ваш внесок отримано!\n"),
    "📅 {dt} 🕘 {time}",
    "👤 {description}",
    "🧾 " + hlink("{title}", "{url}") + "\n",
    "💰 Сума: {amount}",
    "〰〰〰〰〰〰〰",
    "🏃‍♂️ Дякуємо, що біжите разом із нами! 💖",
    sep="\n",
)
