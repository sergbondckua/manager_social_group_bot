import calendar
import logging
import re
from datetime import datetime, timedelta, date
from typing import List, Tuple, Optional, Type, Any, Dict

import monobank

from bank.models import MonoBankCard
import bank.resources.bot_msg_templates as bmt
from bank.services.utils import retry_on_many_requests

logger = logging.getLogger("monobank")


class MonobankService:
    """Клас для роботи з Monobank API."""

    def __init__(self, token: str):
        self.token = token
        self.client = monobank.Client(token=token)

    @retry_on_many_requests(retries=3, delay=15)
    def get_account_statements(
        self,
        account: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[dict]:
        """
        Отримує список транзакцій за вказаними параметрами.

        :param account: Номер рахунку для отримання транзакцій.
        :param date_from: Початкова дата у форматі datetime. Якщо не вказано, використовується -30 днів від поточної дати.
        :param date_to: Кінцева дата у форматі datetime. Якщо не вказано, використовується поточна дата.
        :return: Список транзакцій у вигляді словників.
        """
        # Значення за замовчуванням для timestamp
        now = datetime.now().date()
        if date_from is None:
            date_from = now.replace(day=1)
        if date_to is None:
            _, last_day = calendar.monthrange(now.year, now.month)
            date_to = now.replace(day=last_day)

        return self.client.get_statements(account, date_from, date_to)

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

    DEFAULT_DESCRIPTION = "Не зазначено"
    DEFAULT_COMMENT = "---"
    DEFAULT_RECEIPT_ID = "-x-x-"

    def __init__(self, data: dict):
        self._data = data
        self._statement_item = data.get("statementItem", {})

    def _get_value(self, key: str, default=None, fallback_key: str = None):
        """Отримання значення з основного або додаткового джерела."""
        if self._statement_item:
            return self._statement_item.get(key, default)
        return self._data.get(fallback_key or key, default)

    @property
    def amount(self) -> float:
        return float(self._get_value("amount", 0)) / 100

    @property
    def balance(self) -> float:
        return float(self._get_value("balance", 0)) / 100

    @property
    def description(self) -> str:
        return self._get_value("description", self.DEFAULT_DESCRIPTION)

    @property
    def comment(self) -> str:
        return self._get_value("comment", self.DEFAULT_COMMENT)

    @property
    def receipt_id(self) -> str:
        return self._get_value(
            "receiptId", self.DEFAULT_RECEIPT_ID, fallback_key="id"
        )

    @property
    def commission_rate(self) -> float:
        return float(self._get_value("commissionRate", 0))

    @property
    def timestamp(self) -> int:
        return int(self._get_value("time", 0))


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

    @property
    def formatted_datetime(self) -> str:
        return self._date_time.strftime("%d.%m.%Y %H:%M:%S")


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


class MonoBankContextFormatter:
    """Клас для форматування контексту."""

    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data

    def format_context(self) -> List[Dict[str, Any]]:
        """
        Форматує контекст, відфільтровуючи необхідні поля для кожної транзакції.

        :return: Відформатований список транзакцій.
        """
        return (
            [self._filtered_data(item) for item in self.data]
            if self.data
            else []
        )

    @staticmethod
    def _filtered_data(transaction: dict[str, Any]) -> dict[str, Any]:
        """
        Форматує окрему транзакцію, залишаючи лише необхідні поля.

        :param transaction: Дані однієї транзакції.
        :return: Відфільтровані дані транзакції.
        """
        if not transaction:
            return {}

        # Ініціалізуємо парсер для обробки транзакції
        trans = TransactionDataParser(transaction)

        # Форматуємо час за допомогою DateTimeFormatter
        dt_formatter = DateTimeFormatter(trans.timestamp)

        return {
            "time": dt_formatter.formatted_datetime,  # Форматований час
            "description": trans.description,  # Опис транзакції
            "comment": trans.comment,  # Коментар (якщо є)
            "amount": trans.amount,  # Сума транзакції
            "commission": trans.commission_rate,  # Комісія
            "balance": trans.balance,  # Баланс
        }
