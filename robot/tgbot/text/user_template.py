from aiogram.utils.markdown import text, hbold, hcode

msg_my_id: str = text(
    "Ваша інформація:\n",
    hbold("🚻 ПІБ:") + " {full_name}",
    hbold("🪪 Username:") + hcode(" {username}"),
    hbold("🆔 Ваш ID:") + hcode(" {user_id}"),
    hbold("💬 Чат ID:") + hcode(" {chat_id}"),
    hbold("🔸 Заголовок:") + hcode(" {title}"),
    sep="\n",
)
