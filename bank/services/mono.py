import logging
import re
from datetime import datetime
from typing import NoReturn, List, Tuple, Optional, Type

import monobank
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramAPIError

from bank.models import MonoBankCard

logger = logging.getLogger("monobank")


class MonobankService:
    def __init__(self, token: str):
        """Ініціалізація класу MonobankService."""

        self.token = token
        self.client = monobank.Client(token=token)

    def setup_webhook(self, webhook_url: str) -> NoReturn:
        """Налаштування вебхука Monobank."""
        try:
            client_info = self.client.get_client_info()
            if not client_info.get("webHookUrl"):
                self.client.create_webhook(url=webhook_url)
                logger.info("Webhook successfully created")
            else:
                logger.info("Webhook is already configured")
        except monobank.TooManyRequests as e:
            logger.error("Rate limit exceeded: %s. Retrying later...", e)
        except monobank.Error as e:
            logger.error("API error occurred: %s", e)

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
        return self._date_time.strftime("%d %B %Y р.")

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
        return (
            f"💬 {self.parser.comment}\n"
            f"💰 Сума: {self.parser.amount:.2f}\n"
            f"💵 Баланс: {self.parser.balance:.2f}\n"
            "〰〰〰〰〰〰〰"
        )


class IncomeMessageTemplate(MessageTemplate):
    """Шаблон для повідомлення про надходження"""

    @property
    def message(self) -> str:
        return (
            "✅ Зараз відбулось надходження!\n\n"
            f"📅 {self.dt_formatter.formatted_date} 🕘 {self.dt_formatter.formatted_time}\n"
            f"💳 {self.parser.description}\n"
            f"{self.common_part}"
        )


class ExpenseMessageTemplate(MessageTemplate):
    """Шаблон для повідомлення про витрату"""

    @property
    def message(self) -> str:
        return (
            "🔻 Щойно були витрачені кошти!\n\n"
            f"📅 {self.dt_formatter.formatted_date} 🕘 {self.dt_formatter.formatted_time}\n"
            f"🛍 Кому: {self.parser.description}\n"
            f"🧾 <a href='https://check.gov.ua/'>{self.parser.receipt_id}</a>\n"
            f"{self.common_part}"
        )


class PayerMessageTemplate(MessageTemplate):
    @property
    def message(self) -> str:
        return (
            "✅ Дякую! Ваш внесок отримано!\n\n"
            f"📅 {self.dt_formatter.formatted_date} 🕘 {self.dt_formatter.formatted_time}\n"
            f"👤 {self.parser.description}\n"
            f"🧾 <a href='https://check.gov.ua/'>{self.parser.receipt_id}</a>\n\n"
            f"💰 Сума: {self.parser.amount:.2f}\n"
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
            record = self.db_model.objects.get(card_id=self.account)
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


class TelegramMessageSender:
    """Клас для відправлення повідомлень в Telegram"""

    def __init__(self, token: str):
        self.token = token
        self.bot = Bot(
            token=self.token, default=DefaultBotProperties(parse_mode="HTML")
        )

    async def send_message(
        self, message: str, chat_ids: List[int] | None
    ) -> bool:
        """
        Відправляє повідомлення в зазначені чати
        Повертає статус відправлення (True/False)
        """
        if not chat_ids:
            return False

        success = False
        for chat_id in chat_ids:
            try:
                async with self.bot as bot:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                    )
                success = True
            except TelegramAPIError as e:
                logger.error(
                    "Помилка відправлення повідомлення для %s: %s", chat_id, e
                )
        return success
