from aiogram.utils.markdown import text, hbold


greeting_text = text(
    "✅ {today}",
    "🎊 Сьогодні день народження святкує",
    "👤 " + hbold("{name}"),
    "〰️〰️〰️💙💛🇺🇦💙💛〰️〰️〰️",
    "🍰 {greeting}",
    "〰️〰️〰️🎁🎈🎊🎂💐〰️〰️〰️",
    sep="\n\n",
)
