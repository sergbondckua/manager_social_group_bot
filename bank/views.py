import json
import logging

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from bank.models import MonoBankClient, MonoBankCard
from bank.services.mono import (
    MonobankService,
    MonoBankMessageFormatter,
    MonoBankChatIDProvider,
    MonoBankContextFormatter,
)
from bank.tasks import send_telegram_message

logger = logging.getLogger("monobank-webhook")


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
    """Обробляє webhook від Monobank."""

    def get(self, request, *args, **kwargs):
        return JsonResponse({"status": "method not allowed"}, status=405)

    def post(self, request, *args, **kwargs):
        try:
            body = request.body.decode("utf-8")
            data = json.loads(body)
            event_type = data.get("type")

            if event_type == "StatementItem":
                self._handle_statement_item(data)
            else:
                logger.info("Невідповідний тип подій: %s", event_type)
            return JsonResponse({"status": "success"})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    @staticmethod
    def _handle_statement_item(data: dict) -> None:
        """Обробляє подію StatementItem."""
        transaction_data = data.get("data", {})
        formatter = MonoBankMessageFormatter(transaction_data)
        message = formatter.format_message()
        chat_id_provider = MonoBankChatIDProvider(
            account=transaction_data["account"],
            db_model=MonoBankCard,
            admins=settings.ADMINS_BOT,
        )
        chat_ids = chat_id_provider.get_chat_ids()
        payer_chat_id = chat_id_provider.get_payer_chat_id(
            transaction_data["statementItem"].get("comment")
        )

        # Викликаємо Celery задачу для надсилання повідомлення
        send_telegram_message.delay(message, chat_ids, payer_chat_id)

        # Відправляємо Celery задачу для повідомлення платникам
        if payer_chat_id and chat_ids:
            payer_message = formatter.format_payer_message()
            send_telegram_message.delay(payer_message, [payer_chat_id])


@method_decorator(staff_member_required, name="dispatch")
class MonobankStatementView(View):
    template_name = "admin/monobank_statement.html"

    def get(self, request, *args, **kwargs):
        try:
            query = MonoBankCard.objects.first()
            token = query.client.client_token
            card_id = query.card_id
        except MonoBankCard.DoesNotExist:
            token = ""
            card_id = ""
        context = {}
        # API логіка
        try:
            data = MonobankService(token).get_account_statements(card_id)
        except Exception as e:
            logger.error("API error occurred: %s", e)
            data = [{"error": str(e)}]
        clear_data = MonoBankContextFormatter(data).format_context()
        context["transactions"] = clear_data
        return render(request, self.template_name, context)
