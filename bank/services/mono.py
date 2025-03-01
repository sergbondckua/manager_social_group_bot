import logging
import re
from datetime import datetime
from typing import NoReturn, List, Tuple, Optional, Type

import monobank
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from bank.models import MonoBankCard
import bank.resources.bot_msg_templates as bmt
from common.utils import clean_tag_message
from core.settings import DEFAULT_CHAT_ID

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

    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_message(
        self, message: str, chat_ids: List[int], photo: Optional[str] = None
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
                if photo:
                    await self.bot.send_chat_action(
                        chat_id=chat_id, action="upload_photo"
                    )
                    await self.bot.send_photo(
                        chat_id=chat_id,
                        photo=photo,
                        caption=clean_tag_message(message)[:1024],
                        parse_mode="HTML",
                    )
                else:
                    await self.bot.send_chat_action(
                        chat_id=chat_id, action="typing"
                    )
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=clean_tag_message(message)[:4096],
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                    )
                success = True
            except TelegramAPIError as e:
                logger.error(
                    "Помилка відправлення повідомлення для %s: %s", chat_id, e
                )
        return success

    async def get_user_profile_photo(self, user_id: int) -> Optional[str]:
        """Отримує фото профілю користувача"""

        photos = await self.bot.get_user_profile_photos(user_id)
        if photos.total_count > 0:
            # Отримуємо перше фото (найбільшого розміру)
            photo = photos.photos[0][-1]
            file_id = photo.file_id
            return file_id
        else:
            return None

    async def is_user_in_group(
        self, user_id: int, group_id: int = DEFAULT_CHAT_ID
    ) -> bool:
        """Перевіряє, чи є користувач учасником групи."""

        try:
            member = await self.bot.get_chat_member(group_id, user_id)
            # Якщо користувач є учасником групи, повертаємо True
            return member.status in ["member", "administrator", "creator"]
        except Exception as e:
            logger.error("Помилка при отриманні статусу користувача: %s", e)
            return False
