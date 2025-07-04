from aiogram.utils.markdown import text, hbold

# Текст для часткового прогнозу
part_forecast_text = text(
    "🕗 " + hbold('{forecast_time} 🌡 {temperature}°C 🌬 {wind}м/с'),
    text(
        "▫️ {weather_description}",
        "{precipitation_info}",
    ),
    sep="\n",
)

# Основний текст прогнозу
forecast_text = text(
    "{recipient_text}\n",
    text("🌆 {city}, {country}, 📆 {current_date}"),
    "➖ ➖ ➖ \n",
    "{formatted_data}\n",
    "🫧 /weather_now",
    sep="\n",
)
