from aiogram.utils.markdown import text, hbold, hlink


greeting_text = text(
    "✅ {today}",
    "🎊 Сьогодні день народження святкує",
    "👤 " + hbold("{name}"),
    "〰️〰️〰️💙💛🇺🇦💙💛〰️〰️〰️",
    "🍰 {greeting}",
    "〰️〰️〰️🎁🎈🎊🎂💐〰️〰️〰️",
    sep="\n\n",
)
