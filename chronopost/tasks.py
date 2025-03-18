import asyncio
import logging

from asgiref.sync import sync_to_async

from chronopost.models import WeatherNotification
import chronopost.resources.bot_msg_templates as bmt
from chronopost.services.weather import (
    OpenWeatherClient,
    WeatherProcessor,
    WeatherFormatter,
    TelegramNotifier,
)
from core.settings import WEATHER_API_KEY, CITY_COORDINATES
from celery import shared_task


from chronopost.services.schedulers import MessageScheduler
from robot.config import ROBOT

logger = logging.getLogger("chronopost")


@shared_task(expires=10)
def send_scheduled_messages() -> None:
    """Завдання Celery для надсилання запланованих повідомлень."""

    async def main() -> None:
        async with ROBOT as bot:
            scheduler = MessageScheduler(bot)
            await scheduler.process_messages()

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except Exception as e:
        logger.error("Помилка виконання основного циклу asyncio: %s", e)


@shared_task(expires=86000)
def send_weather_forecast():
    """Завдання Celery для надсилання прогнозу погоди."""

    @sync_to_async
    def fetch_receivers():
        """Асинхронно отримуємо активних підписників."""
        return list(WeatherNotification.objects.filter(is_active=True))

    async def fetch_and_process_weather():
        """Отримання та обробка прогнозу погоди."""

        api_client = OpenWeatherClient(WEATHER_API_KEY)
        raw_data = await api_client.fetch_weather_data(CITY_COORDINATES)

        if not raw_data:
            logger.warning("No data from API")
            return None

        processor = WeatherProcessor(filter_precipitation=True)
        clear_data = processor.filter_weather_data(raw_data)

        if not clear_data:
            logger.warning("No data after filtration")
            return None

        presenter = WeatherFormatter(include_today_only=True)
        formatted_data = presenter.format_weather_report(clear_data)

        if not formatted_data:
            logger.warning("No data after formatting")
            return None

        return {
            "city": raw_data.get("city", {}).get("name", "Unknown City"),
            "country": raw_data.get("city", {}).get(
                "country", "Unknown Country"
            ),
            "formatted_data": formatted_data,
        }

    async def send_notifications(receivers, weather_data):
        """Надсилання повідомлень користувачам."""

        for recipient in receivers:
            notifier = TelegramNotifier(ROBOT, recipient.chat_id)
            message = bmt.forecast_text.format(
                recipient_text=recipient.text,
                city=weather_data["city"],
                country=weather_data["country"],
                formatted_data=" ".join(weather_data["formatted_data"]),
            )

            try:
                await notifier.send_message(
                    text=message, poster=recipient.poster
                )
            except Exception as e:
                logger.error(
                    f"Failed to send message to {recipient.chat_id}: {e}"
                )

    async def main():
        receivers = await fetch_receivers()
        if not receivers:
            logger.info("There are no active subscriptions")
            return {"status": "success", "message": "Немає активних підписок"}

        weather_data = await fetch_and_process_weather()
        if not weather_data:
            return {
                "status": "error",
                "message": "Помилка обробки даних погоди",
            }
        await send_notifications(receivers, weather_data)
        return {
            "status": "success",
            "message": "Повідомлення успішно надіслано",
        }

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except Exception as e:
        logger.error("Помилка виконання основного циклу asyncio: %s", e)
