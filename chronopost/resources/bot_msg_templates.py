from aiogram.utils.markdown import text, hbold
from django.utils import timezone

part_forecast_text = text(
    "🕗 " + hbold("{forecast_time} 🌡 {temperature}°C "),
    text(
        "🔸 {weather_description}" "☂️ {precipitation_info}\n\n",
        sep="\n",
    ),
    sep="\n",
)
forecast_text = text(
    "{recipient_text}",
    "➖ ➖ ➖",
    "🌆 {city}, {country}",
    f"📆 {timezone.localtime(timezone.now()).date().strftime('%d.%m.%Y')}\n",
    "{formatted_data}",
    sep="\n",
)
