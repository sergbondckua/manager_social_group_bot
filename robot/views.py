import json
import logging

from django.utils.decorators import method_decorator
from django.views import View
from django.http import HttpResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt

from robot import bot as robot

logger = logging.getLogger("robot")


@method_decorator(csrf_exempt, name="dispatch")
class WebhookView(View):
    """Обробляє webhook-запити від Telegram."""

    async def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        return HttpResponse("OK", status=200)

    async def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        try:
            update_data = json.loads(request.body)
            logger.info("Отримано оновлення: %s", update_data)
            # Асинхронно передаємо оновлення до диспетчера бота
            await robot.feed_update(update_data)
            logger.debug("Отримано оновлення: %s", update_data)

            return HttpResponse(status=200)
        except json.JSONDecodeError as e:
            logger.error("Помилка декодування JSON: %s", e)
            return HttpResponse("Невірний формат JSON", status=400)
        except Exception as e:
            logger.exception("Неочікувана помилка при обробці webhook")
            return HttpResponse("Внутрішня помилка сервера", status=500)
