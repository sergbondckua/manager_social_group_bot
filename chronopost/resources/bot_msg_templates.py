from aiogram.utils.markdown import text, hbold

# Текст для часткового прогнозу
part_forecast_text = text(
    f"🕗 {hbold('{forecast_time} 🌡 {temperature}°C')}",
    text(
        "🔸 {weather_description}",
        "{precipitation_info}",
    ),
    sep="\n",
)

# Основний текст прогнозу
forecast_text = text(
    "{recipient_text}",
    "🫧",
    text("🌆 {city}, {country}, 📆 {current_date}"),
    "➖ ➖ ➖ \n",
    "{formatted_data}",
    sep="\n",
)
