from aiogram.utils.markdown import text, hbold
from django.utils import timezone

# Форматування часу
current_date = timezone.localtime(timezone.now()).date().strftime("%d.%m.%Y")

# Текст для часткового прогнозу
part_forecast_text = text(
    f"🕗 {hbold('{forecast_time} 🌡 {temperature}°C')}",
    text(
        "🔸 {weather_description}",
        "☂️ {precipitation_info}",
        sep="\n",
    ),
    sep="\n",
)

# Основний текст прогнозу
forecast_text = text(
    "{recipient_text}",
    "➖ ➖ ➖",
    "🌆 {city}, {country}",
    f"📆 {current_date}",
    "{formatted_data}",
    sep="\n",
)
