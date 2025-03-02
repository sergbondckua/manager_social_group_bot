from aiogram.utils.markdown import text, hbold


part_forecast_text = text(
    "🕗 " + hbold("{forecast_time}"),
    text(
        "    🔸 {weather_description}",
        "🌡 {temperature}°C ",
        "☂️ {precipitation_info}",
    ),
    sep="\n",
)
forecast_text = text(
    "{recipient_text}",
    "➖ ➖ ➖",
    "🌆 {city}, {country}\n",
    "{formatted_data}",
    sep="\n",
)
