from typing import Tuple

from django.utils import timezone

import chronopost.resources.bot_msg_templates as bmt
from aiogram.types import Message
from chronopost.services.weather import OpenWeatherClient
from chronopost.services.weather import WeatherProcessor, WeatherFormatter


class WeatherNowHandler:
    def __init__(
        self,
        message: Message,
        weather_api_key: str,
        city_coordinates: Tuple[float, float],
    ):
        self.message = message
        self.api_client = OpenWeatherClient(weather_api_key)
        self.city_coordinates = city_coordinates
        self.weather_processor = WeatherProcessor(filter_precipitation=False)
        self.weather_formatter = WeatherFormatter(include_today_only=True)

    async def fetch_weather_data(self):
        """Отримує дані погоди з API."""
        try:
            return await self.api_client.fetch_weather_data(
                self.city_coordinates
            )
        except Exception as e:
            await self.message.answer(
                "Помилка під час запиту до API: {}".format(e)
            )
            return

    async def process_weather_data(self, raw_data):
        """Обробляє сирі дані погоди."""
        try:
            return self.weather_processor.filter_weather_data(raw_data)
        except Exception as e:
            await self.message.answer("Помилка обробки даних: {}".format(e))
            return

    async def format_weather_data(self, clear_data):
        """Форматує дані для відображення."""
        try:
            if formatted_data := self.weather_formatter.format_weather_report(
                clear_data
            ):
                return formatted_data
            else:
                return ("🌘 У цей час доби прогноз погоди не відображається",)
        except Exception as e:
            await self.message.answer(
                "Помилка форматування даних: {}".format(e)
            )
            return

    async def send_weather_report(self, weather_data, formatted_data):
        """Надсилає користувачеві повідомлення про погоду."""
        
        try:
            weather_message = bmt.forecast_text.format(
                recipient_text="🔹 Погода зараз 🔹",
                city=weather_data["city"],
                country=weather_data["country"],
                current_date=weather_data["current_date"],
                formatted_data="\n\n".join(formatted_data),
            )
            await self.message.bot.send_chat_action(
                self.message.from_user.id, "typing"
            )
            await self.message.bot.send_message(
                self.message.from_user.id, weather_message
            )
        except Exception as e:
            await self.message.answer(
                "Не вдалося надіслати повідомлення: {}".format(e)
            )

    async def handle(self):
        """Основний метод для обробки запиту."""
        raw_data = await self.fetch_weather_data()
        if not raw_data:
            return

        clear_data = await self.process_weather_data(raw_data)
        if not clear_data:
            return

        formatted_data = await self.format_weather_data(clear_data)
        if not formatted_data:
            return

        weather_data = {
            "city": raw_data.get("city", {}).get("name", "Unknown City"),
            "country": raw_data.get("city", {}).get(
                "country", "Unknown Country"
            ),
            "current_date": timezone.localtime(timezone.now())
            .date()
            .strftime("%d.%m.%Y"),
        }
        await self.send_weather_report(weather_data, formatted_data)
