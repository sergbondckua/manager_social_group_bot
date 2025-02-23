import logging
import aiohttp
import asyncio
from datetime import datetime, time
from typing import Dict, List, Optional, Tuple, Any

from aiogram import Bot
from aiogram.types import FSInputFile

from chronopost.utils import clean_tag_message

logger = logging.getLogger("weather_api")


class OpenWeatherClient:
    """Асинхронний клієнт для роботи з OpenWeatherMap API."""

    BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def fetch_weather_data(
        self, coordinates: Tuple[float, float]
    ) -> Optional[Dict]:
        """Отримує прогноз погоди для заданих координат."""
        logger.info("Запит погоди для координат %s", coordinates)

        if not self._is_valid_coordinates(coordinates):
            logger.error("Некоректні координати: %s", coordinates)
            return None

        params = {
            "lat": coordinates[0],
            "lon": coordinates[1],
            "appid": self.api_key,
            "units": "metric",
            "lang": "uk",
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    url=self.BASE_URL,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    response.raise_for_status()
                    return await response.json()
            except asyncio.TimeoutError:
                logger.error(
                    "Перевищено час очікування для координат %s", coordinates
                )
            except aiohttp.ClientError as error:
                logger.error("Помилка запиту для %s: %s", coordinates, error)

        return None

    @staticmethod
    def _is_valid_coordinates(coordinates: Tuple[float, float]) -> bool:
        """Перевіряє валідність координат."""
        return len(coordinates) == 2 and all(
            isinstance(coord, (float, int)) for coord in coordinates
        )


class WeatherProcessor:
    """Клас для обробки даних прогнозу погоди."""

    def __init__(self, *, filter_precipitation: bool = False):
        self.filter_precipitation = filter_precipitation

    @staticmethod
    def has_precipitation(weather_entry: Dict) -> bool:
        """Перевіряє, чи містить запис інформацію про опади."""
        return "rain" in weather_entry or "snow" in weather_entry

    def filter_weather_data(self, raw_data: Optional[Dict]) -> List[Dict]:
        """Фільтрує записи за наявністю опадів."""

        if not raw_data or "list" not in raw_data:
            return []

        forecasts = raw_data["list"]
        return [
            entry
            for entry in forecasts
            if not self.filter_precipitation or self.has_precipitation(entry)
        ]


class WeatherFormatter:
    """Клас для форматування прогнозу погоди у зручний вигляд."""

    def __init__(self, *, include_today_only: bool = False):
        self.include_today_only = include_today_only

    def format_weather_report(self, forecasts: List[Dict]) -> List[str]:
        """Форматує список прогнозів у текстовий вигляд, фільтруючи порожні записи."""

        logger.debug("Початок форматування %d прогнозів", len(forecasts))
        return [
            formatted
            for entry in forecasts
            if (
                formatted := self._format_forecast(
                    entry, self.include_today_only
                )
            )
        ]

    def _format_forecast(
        self, entry: Dict[str, Any], include_today_only: bool = False
    ) -> str:
        """Форматує один запис прогнозу погоди у вигляді рядка.

        Args:
            entry: Словник з даними прогнозу. Очікує наявність ключів 'dt', 'main', 'weather'.
            include_today_only: Якщо True, включає лише записи за поточний день.

        Returns:
            Відформатований рядок або порожній рядок, якщо запис не відповідає фільтру.
        """

        forecast_date_time = datetime.fromtimestamp(entry.get("dt", 0))

        if include_today_only and not self._is_within_today_range(
            forecast_date_time
        ):
            return ""

        # Форматуємо час в зручний вигляд в залежності від include_today_only
        if include_today_only:
            forecast_time = forecast_date_time.time().strftime("%H:%M")
        else:
            forecast_time = forecast_date_time.strftime("%Y-%m-%d %H:%M")

        precipitation_info = self._extract_precipitation(entry)
        weather_description = (
            entry.get("weather", [{}])[0]
            .get("description", "немає опису")
            .capitalize()
        )
        temperature = round(float(entry.get("main", {}).get("temp", "N/A")), 1)

        return (
            f"🕗 <b>{forecast_time}</b> :\n"
            f"    🔸 {weather_description}"
            f"🌡 {temperature}°C "
            f"☂️ {precipitation_info or 'немає'}\n"
        )

    @staticmethod
    def _is_within_today_range(forecast_time: datetime) -> bool:
        """Перевіряє, чи прогноз належить до поточного дня у межах 08:00-21:00."""
        today = datetime.today().date()
        today_8am = datetime.combine(today, time(8, 0)).timestamp()
        today_9pm = datetime.combine(today, time(21, 0)).timestamp()
        return (
            today == forecast_time.date()
            and today_8am <= forecast_time.timestamp() <= today_9pm
        )

    @staticmethod
    def _extract_precipitation(entry: Dict) -> str:
        """Отримує інформацію про опади у форматі тексту."""
        precipitation = []
        for precip_type, label in {"rain": "Дощ", "snow": "Сніг"}.items():
            if precip_data := entry.get(precip_type):
                precipitation.append(f"{label}: {precip_data.get('3h', 0)} мм")
        return ", ".join(precipitation)


class TelegramNotifier:
    """Нотифікація через Telegram"""

    def __init__(self, bot: Bot, chat_id: int | str):
        self.bot = bot
        self.chat_id = chat_id

    async def send_message(self, text: str, poster=None):
        """Надсилає повідомлення в Telegram"""

        logger.info("Спроба надіслати повідомлення до чату %s", self.chat_id)

        try:
            async with self.bot as bot:
                if poster:
                    photo_file = FSInputFile(poster.path)
                    await self.bot.send_chat_action(
                        chat_id=self.chat_id, action="upload_photo"
                    )
                    await self.bot.send_photo(
                        chat_id=self.chat_id,
                        photo=photo_file,
                        caption=clean_tag_message(text[:1024]),
                    )
                else:
                    await self.bot.send_chat_action(
                        chat_id=self.chat_id, action="typing"
                    )
                    await bot.send_message(
                        chat_id=self.chat_id, text=clean_tag_message(text[:4096])
                    )
            logger.info("Message sent to chat %s", self.chat_id)
        except Exception as e:
            logger.error("Failed to send message: %s", e)
