from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from django.conf import settings
from django.utils import timezone

from chronopost.services.weather import (
    OpenWeatherClient,
    WeatherProcessor,
    WeatherFormatter,
)
from robot.tgbot.text.user_template import msg_my_id
import chronopost.resources.bot_msg_templates as bmt

user_router = Router()


@user_router.message(CommandStart())
async def admin_start(message: Message):
    await message.reply(
        f"Вітаю, {message.from_user.mention_html(message.from_user.first_name)}!"
    )


@user_router.message(Command(commands=["myid", "my_id"]))
async def handle_my_id(message: Message):
    await message.answer(
        msg_my_id.format(
            user_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username or "",
            chat_id=message.chat.id,
            title=message.chat.title or message.from_user.full_name,
        )
    )


@user_router.message(Command(commands=["weathernow", "weather_now"]))
async def handle_weather_now(message: Message):
    """Показує поточну погоду в місті"""

    user_id = message.from_user.id

    # Отримуємо дані погоди
    api_client = OpenWeatherClient(settings.WEATHER_API_KEY)
    raw_data = await api_client.fetch_weather_data(settings.CITY_COORDINATES)

    if not raw_data:
        await message.bot.send_message(user_id, "Щось пішло не так з API")
        return

    # Обробляємо дані
    processor = WeatherProcessor(filter_precipitation=False)
    clear_data = processor.filter_weather_data(raw_data)

    if not clear_data:
        await message.bot.send_message(
            user_id, "Щось пішло не так з обробкою даних"
        )
        return

    # Виводимо дані
    presenter = WeatherFormatter(include_today_only=True)
    formatted_data = presenter.format_weather_report(clear_data)

    if not formatted_data:
        await message.bot.send_message(
            user_id, "Щось пішло не так з форматуванням даних"
        )
        return

    # Створюємо повідомлення
    weather_data = {
        "city": raw_data.get("city", {}).get("name", "Unknown City"),
        "country": raw_data.get("city", {}).get("country", "Unknown Country"),
        "current_date": timezone.localtime(timezone.now())
        .date()
        .strftime("%d.%B.%Y"),
        "formatted_data": formatted_data,
    }

    # Надсилання повідомлення
    await message.bot.send_chat_action(user_id, "typing")
    await message.bot.send_message(
        user_id,
        bmt.forecast_text.format(
            recipient_text="Погода зараз",
            city=weather_data["city"],
            country=weather_data["country"],
            current_date=weather_data["current_date"],
            formatted_data="\n\n".join(weather_data["formatted_data"]),
        ),
    )
