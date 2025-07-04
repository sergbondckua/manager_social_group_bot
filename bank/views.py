import calendar
import json
import logging
from datetime import datetime
from typing import NoReturn, Tuple, Optional, List

import monobank
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from bank.forms import MonobankStatementForm
from bank.models import MonoBankClient, MonoBankCard
from bank.services.mono import (
    MonobankService,
    MonoBankMessageFormatter,
    MonoBankChatIDProvider,
    MonoBankContextFormatter,
)
from bank.tasks import send_telegram_message
from common.utils import get_personalized_compliment_message

logger = logging.getLogger("monobank-webhook")


class GetApiCardsView(PermissionRequiredMixin, View):
    """Отримує список карток для вибраного клієнта з monobank api."""

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


class GetCardsView(PermissionRequiredMixin, View):
    """Повертає картки для обраного клієнта у форматі JSON"""

    permission_required = "bank.view_monobankclient"

    def get(self, request, client_id, *args, **kwargs):
        cards = MonoBankCard.objects.filter(
            client_id=client_id, is_active=True
        )
        data = {
            "cards": [
                {"id": card.id, "card_id": card.card_id} for card in cards
            ]
        }
        return JsonResponse(data)


@method_decorator(csrf_exempt, name="dispatch")
class MonobankWebhookView(View):
    """Обробляє webhook від Monobank."""

    def get(self, request, *args, **kwargs):
        return JsonResponse({"status": "method not allowed"}, status=405)

    def post(self, request, *args, **kwargs):
        try:
            data = self._parse_request_body(request)
            self._validate_event_type(data)

            if data["type"] == "StatementItem":
                self._handle_statement_item(data)

            return JsonResponse({"status": "success"}, status=200)
        except json.JSONDecodeError:
            logger.error("Отримано некоректний JSON")
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except ValueError as e:
            logger.error("Помилка валідації даних: %s", e)
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            logger.exception("Неочікувана помилка")
            return JsonResponse({"error": str(e)}, status=500)

    @staticmethod
    def _parse_request_body(request) -> dict:
        """Розбирає тіло запиту."""
        try:
            body = request.body.decode("utf-8")
            return json.loads(body)
        except UnicodeDecodeError:
            raise ValueError("Не вдалося декодувати тіло запиту")

    @staticmethod
    def _validate_event_type(data: dict):
        """Валідує тип події."""
        if "type" not in data:
            raise ValueError("Відсутній ключ 'type'")
        if data["type"] not in ["StatementItem"]:
            raise ValueError(f"Невідповідний тип події: {data['type']}")

    def _handle_statement_item(self, data: dict) -> NoReturn:
        """Обробляє подію StatementItem."""
        transaction_data = self._extract_transaction_data(data)
        formatter = MonoBankMessageFormatter(transaction_data)

        chat_ids, payer_chat_id = self._get_chat_ids(transaction_data)
        self._send_notifications(formatter, chat_ids, payer_chat_id)

    @staticmethod
    def _extract_transaction_data(data: dict) -> dict:
        """Виділяє дані транзакції."""
        transaction_data = data.get("data", {})
        if (
            "account" not in transaction_data
            or "statementItem" not in transaction_data
        ):
            raise ValueError("Некоректна структура даних транзакції")
        return transaction_data

    @staticmethod
    def _get_chat_ids(
        transaction_data: dict,
    ) -> Tuple[List[int], Optional[int]]:
        """Отримує список ID чатів."""
        chat_id_provider = MonoBankChatIDProvider(
            account=transaction_data["account"],
            db_model=MonoBankCard,
            admins=settings.ADMINS_BOT,
        )
        chat_ids = chat_id_provider.get_chat_ids()
        payer_chat_id = chat_id_provider.get_payer_chat_id(
            transaction_data["statementItem"].get("comment")
        )
        return chat_ids, payer_chat_id

    @staticmethod
    def _send_notifications(
        formatter: MonoBankMessageFormatter,
        chat_ids: List[int],
        payer_chat_id: Optional[int],
    ) -> NoReturn:
        """Надсилає повідомлення через Celery."""
        message = formatter.format_message()
        send_telegram_message.delay(message, chat_ids)

        if payer_chat_id:
            payer_message = formatter.format_payer_message()
            compliment_payer_message = get_personalized_compliment_message()
            send_telegram_message.delay(payer_message, [payer_chat_id])
            send_telegram_message.delay(
                compliment_payer_message,
                [settings.DEFAULT_CHAT_ID],
                payer_chat_id,
            )


@method_decorator(staff_member_required, name="dispatch")
class MonobankStatementView(View):
    template_name = "admin/monobank_statement.html"

    @staticmethod
    def _get_initial_data():
        """Отримання початкових даних для форми."""
        query = MonoBankCard.objects.select_related("client").first()
        now = datetime.now().date()

        def get_month_date_range(date):
            """Отримати перший та останній день місяця."""
            _, last_day = calendar.monthrange(date.year, date.month)
            return date.replace(day=1), date.replace(day=last_day)

        date_from, date_to = (
            d.strftime("%Y-%m-%d") for d in get_month_date_range(now)
        )

        if not query:
            return {
                "client_id": "",
                "token": "",
                "card_id": "",
                "date_from": "",
                "date_to": "",
            }

        return {
            "client_id": query.client_id,
            "token": query.client.client_token,
            "card_id": query.card_id,
            "date_from": date_from,
            "date_to": date_to,
        }

    @staticmethod
    def _get_transactions(token, card_id, date_from=None, date_to=None):
        """Отримання транзакцій через Monobank API."""

        try:
            return MonobankService(token).get_account_statements(
                card_id, date_from, date_to
            )
        except monobank.TooManyRequests as e:
            logger.error("Rate limit exceeded: %s", e)
            raise Exception("Rate limit exceeded. Please try again later.")
        except monobank.Error as e:
            logger.error("API error occurred: %s", e)
            raise Exception("API error: " + str(e))
        except Exception as e:
            logger.error("Unexpected error occurred: %s", e)
            raise Exception("Unexpected error: " + str(e))

    def get(self, request, *args, **kwargs):
        """Обробка GET-запиту (відображення форми)."""
        initial_data = self._get_initial_data()

        form = MonobankStatementForm(
            initial={
                "client_token": initial_data.get("client_id", ""),
                "card_id": initial_data.get("card_id", ""),
                "date_from": initial_data.get("date_from", ""),
                "date_to": initial_data.get("date_to", ""),
            }
        )
        context = {"form": form}

        if initial_data.get("token") and initial_data.get("card_id"):
            try:
                data = self._get_transactions(
                    initial_data["token"], initial_data["card_id"]
                )
                context["transactions"] = MonoBankContextFormatter(
                    data
                ).format_context()
            except Exception as e:
                context["errors"] = str(e)

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """Обробка POST-запиту (відправлення форми)."""
        client_id = request.POST.get("client_token")
        form = MonobankStatementForm(request.POST, client_id=client_id)
        context = {"form": form}

        if form.is_valid():
            try:
                client_token = form.cleaned_data["client_token"].client_token
                card_id = form.cleaned_data["card_id"]
                date_from = form.cleaned_data["date_from"]
                date_to = form.cleaned_data["date_to"]

                data = self._get_transactions(
                    client_token, card_id, date_from, date_to
                )
                context["transactions"] = MonoBankContextFormatter(
                    data
                ).format_context()
            except Exception as e:
                context["errors"] = str(e)
        else:
            logger.warning("Форма не пройшла валідацію: %s", form.errors)

        return render(request, self.template_name, context)
