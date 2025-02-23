import json

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from bank.models import MonoBankClient
from bank.services.mono import MonobankService, format_monobank_message


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
            # Отримання даних із запиту
            body = request.body.decode("utf-8")
            data = json.loads(body)

            # Обробка отриманих даних
            event_type = data.get("type")
            if event_type == "StatementItem":
                # Обробка транзакції
                transaction_data = data.get("data", {})
                # Логіка для обробки транзакції
                format_monobank_message(transaction_data)
            else:
                print(f"Unhandled event type: {event_type}")

            # Повертаємо відповідь Monobank
            return JsonResponse({"status": "success"})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
