import json

from django.utils.decorators import method_decorator
from django.views import View
from django.http import HttpResponse, HttpRequest
from aiogram import types
from django.views.decorators.csrf import csrf_exempt

from robot.bot import dp, bot


@method_decorator(csrf_exempt, name="dispatch")
class WebhookView(View):
    """Клас для обробки вебхуків від Telegram"""

    async def post(self, request: HttpRequest) -> HttpResponse:
        # Обробка вхідного POST-запиту
        try:
            json_data = json.loads(request.body.decode("utf-8"))
            telegram_update = types.Update.model_validate(
                json_data, context={"bot": bot}
            )
            await dp.feed_update(bot=bot, update=telegram_update)
            return HttpResponse("OK")

        except json.JSONDecodeError:
            return HttpResponse("Invalid JSON", status=400)

        except Exception as e:
            return HttpResponse(f"Error: {str(e)}", status=500)

    async def get(self, request: HttpRequest) -> HttpResponse:
        """Обробка GET-запитів для перевірки працездатності"""
        return HttpResponse("Webhook is working!", status=200)
