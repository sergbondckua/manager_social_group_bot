import json

from asgiref.sync import async_to_sync
from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from bank.models import MonoBankClient, MonoBankCard
from bank.services.mono import (
    MonobankService,
    MonoBankMessageFormatter,
    MonoBankChatIDProvider,
    TelegramMessageSender,
)
from common.utils import clean_tag_message


class GetCardsView(PermissionRequiredMixin, View):
    """Отримує список карток для вибраного клієнта."""

    permission_required = "bank.view_monobankclient"

    def get(self, request, client_id):
        client = MonoBankClient.objects.filter(pk=client_id).first()
        if not client:
            return JsonResponse({"cards": []}, status=404)

        card_choices = MonobankService(
            client.client_token
        ).get_credit_card_ids()
        return JsonResponse(
            {"cards": [{"id": c[0], "name": c[1]} for c in card_choices]}
        )


@method_decorator(csrf_exempt, name="dispatch")
class MonobankWebhookView(View):
    """Обробляє вебхук Monobank."""

    def get(self, request, *args, **kwargs):
        return JsonResponse({"status": "success"})

    def post(self, request, *args, **kwargs):
        try:
            body = request.body.decode("utf-8")
            data = json.loads(body)

            event_type = data.get("type")
            if event_type == "StatementItem":
                transaction_data = data.get("data", {})
                formatter = MonoBankMessageFormatter(transaction_data)
                message = formatter.format_message()

                chat_id_provider = MonoBankChatIDProvider(
                    account=transaction_data["account"],
                    db_model=MonoBankCard,
                    admins=settings.ADMINS_BOT,
                )
                chat_ids = chat_id_provider.get_chat_ids()

                # Створюємо єдиний sender для всіх операцій
                sender = TelegramMessageSender(
                    token=settings.TELEGRAM_BOT_TOKEN
                )

                # Асинхронно відправляємо повідомлення
                async def send_message():
                    await sender.send_message(
                        clean_tag_message(message), chat_ids
                    )

                    if payer_chat_id := chat_id_provider.get_payer_chat_id(
                        transaction_data["statementItem"].get("comment")
                    ):
                        payer_message = formatter.format_payer_message()
                        await sender.send_message(
                            clean_tag_message(payer_message), [payer_chat_id]
                        )

                # Викликаємо асинхронну функцію
                async_to_sync(send_message)()
            else:
                print(f"Unhandled event type: {event_type}")

            return JsonResponse({"status": "success"})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
