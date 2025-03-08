import logging
import re
from datetime import datetime
from typing import List, Tuple, Optional, Type

import monobank

from bank.models import MonoBankCard
import bank.resources.bot_msg_templates as bmt

logger = logging.getLogger("monobank")


class MonobankService:
    def __init__(self, token: str):
        """Ініціалізація класу MonobankService."""

        self.token = token
        self.client = monobank.Client(token=token)

    def is_webhook_configured(self) -> Optional[str]:
        """Перевіряє, чи налаштований webhook."""
        try:
            client_info = self.client.get_client_info()
            return client_info.get("webHookUrl")
        except Exception as e:
            logger.error("Failed to retrieve client info: %s", e)
            return None

    def create_webhook(self, webhook_url: str) -> bool:
        """Створює webhook за вказаною URL-адресою."""
        try:
            self.client.create_webhook(url=webhook_url)
            logger.info("Webhook successfully created")
            return True
        except monobank.TooManyRequests as e:
            logger.error("Rate limit exceeded: %s. Retrying later...", e)
        except monobank.Error as e:
            logger.error("API error occurred while creating webhook: %s", e)
        except Exception as e:
            logger.error(
                "Unexpected error occurred while creating webhook: %s", e
            )

        return False

    def setup_webhook(self, webhook_url: str) -> bool:
        """Головна функція для налаштування webhook."""
        current_webhook = self.is_webhook_configured()

        if current_webhook:
            logger.info("Webhook is already configured: %s", current_webhook)
            return True

        return self.create_webhook(webhook_url)

    def get_credit_card_ids(self) -> List[Tuple[str, str]]:
        """Отримує ідентифікатори кредитних рахунків та їх деталі."""
        try:
            accounts = self.client.get_client_info().get("accounts", [])
        except monobank.Error as e:
            logger.error("Error occurred: %s", e)
            return []

        card_choices = []
        for account in accounts:
            account_id = account.get("id", "Unknown ID")
            account_type = account.get("type", "Unknown type")
            masked_pan = account.get("maskedPan", ["Unknown maskedPan"])

            card_choices.append(
                (account_id, f"{account_type} - {', '.join(masked_pan)}")
            )

        return card_choices

    def is_token_valid(self) -> bool:
        """Перевіряє, чи дійсний токен."""
        try:
            self.client.get_client_info()
            return True
        except monobank.Error:
            return False


class TransactionDataParser:
    """Клас для отримання та парсингу даних транзакції."""

    def __init__(self, data: dict):
        self._data = data
        self._statement_item = data["statementItem"]

    @property
    def amount(self) -> float:
        return self._statement_item["amount"] / 100

    @property
    def balance(self) -> float:
        return self._statement_item["balance"] / 100

    @property
    def description(self) -> str:
        return self._statement_item.get("description", "Не зазначено")

    @property
    def comment(self) -> str:
        return self._statement_item.get("comment", "---")

    @property
    def receipt_id(self) -> str:
        return self._statement_item.get("receiptId", "-x-x-")

    @property
    def timestamp(self) -> int:
        return self._statement_item["time"]


class DateTimeFormatter:
    """Клас для форматування дати та часу"""

    def __init__(self, timestamp: int):
        self._date_time = datetime.fromtimestamp(timestamp)

    @property
    def formatted_date(self) -> str:
        return self._date_time.strftime("%d.%m.%Y")

    @property
    def formatted_time(self) -> str:
        return self._date_time.strftime("%H:%M:%S")


class MessageTemplate:
    """Базовий клас для шаблонів повідомлень"""

    def __init__(
        self, parser: TransactionDataParser, dt_formatter: DateTimeFormatter
    ):
        self.parser = parser
        self.dt_formatter = dt_formatter

    @property
    def common_part(self) -> str:
        return bmt.common_part_text.format(
            comment=self.parser.comment,
            amount=f"{self.parser.amount:.2f}",
            balance=f"{self.parser.balance:.2f}",
        )


class IncomeMessageTemplate(MessageTemplate):
    """Шаблон для повідомлення про надходження"""

    @property
    def message(self) -> str:
        return bmt.income_text.format(
            dt=self.dt_formatter.formatted_date,
            time=self.dt_formatter.formatted_time,
            description=self.parser.description,
            common_part=self.common_part,
        )


class ExpenseMessageTemplate(MessageTemplate):
    """Шаблон для повідомлення про витрату"""

    @property
    def message(self) -> str:
        return bmt.expense_text.format(
            dt=self.dt_formatter.formatted_date,
            time=self.dt_formatter.formatted_time,
            description=self.parser.description,
            title=self.parser.receipt_id,
            url="https://check.gov.ua/",
            common_part=self.common_part,
        )


class PayerMessageTemplate(MessageTemplate):
    @property
    def message(self) -> str:
        return bmt.payer_text.format(
            dt=self.dt_formatter.formatted_date,
            time=self.dt_formatter.formatted_time,
            description=self.parser.description,
            title=self.parser.receipt_id,
            url="https://check.gov.ua/",
            amount=f"{self.parser.amount:.2f}",
        )


class MonoBankMessageFormatter:
    """Головний клас для форматування повідомлень"""

    def __init__(self, data: dict):
        self.parser = TransactionDataParser(data)
        self.dt_formatter = DateTimeFormatter(self.parser.timestamp)

    def format_message(self) -> str:
        if self.parser.amount > 0:
            template = IncomeMessageTemplate(self.parser, self.dt_formatter)
        else:
            template = ExpenseMessageTemplate(self.parser, self.dt_formatter)
        return template.message

    def format_payer_message(self) -> str:
        template = PayerMessageTemplate(self.parser, self.dt_formatter)
        return template.message


class MonoBankChatIDProvider:
    """
    Надає функціонал для отримання chat_id з бази даних та аналізу коментарів.
    """

    # Компілюємо регулярний вираз
    _USER_ID_PATTERN = re.compile(r"user_id:\s*(\d+)", re.IGNORECASE)

    def __init__(
        self, account: str, db_model: Type[MonoBankCard], admins: List[int]
    ):
        self.account = account
        self.db_model = db_model
        self.admins = admins

    def get_chat_ids(self) -> Optional[List[int]]:
        """Повертає chat_id з бази даних або резервний список адміністраторів."""
        try:
            record = self.db_model.objects.get(
                card_id=self.account, is_active=True
            )
            return [record.chat_id] if record.chat_id else self.admins
        except self.db_model.DoesNotExist:
            return None

    def get_payer_chat_id(self, comment: Optional[str]) -> Optional[int]:
        """Видобуває числовий ідентифікатор платника з коментаря."""
        if not comment:
            return None

        if match := self._USER_ID_PATTERN.search(comment):
            return int(match.group(1))
        return None
