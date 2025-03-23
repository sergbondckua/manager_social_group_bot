from aiogram.utils.markdown import text, hbold, hitalic

# Константи для повторюваних елементів
DOUBLE_TAB = "\t\t"
SEPARATOR = "〰️〰️〰️💙💛🇺🇦💙💛〰️〰️〰️"
FOOTER = "〰️〰️〰️🎁🎈🎊🎂💐〰️〰️〰️"

# Формування тексту вітання
greeting_text = text(
    "✅ {today}",
    "🎊 Сьогодні день народження святкує",
    f"👤 {hbold('{name}')}",
    SEPARATOR,
    f"{DOUBLE_TAB}{hitalic('{greeting}')}",
    FOOTER,
    sep="\n\n",
)
