import logging
from datetime import datetime
from typing import NoReturn, List, Tuple

import monobank

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


def format_monobank_message(data):
    # Отримання даних із JSON
    statement_item = data["statementItem"]

    # Форматування часу
    timestamp = statement_item["time"]
    date_time = datetime.fromtimestamp(timestamp)
    formatted_date = date_time.strftime("%d %B %Y р.")
    formatted_time = date_time.strftime("%H:%M:%S")

    # Форматування даних
    description = statement_item.get("description", "Не зазначено")
    comment = statement_item.get("comment", "---")
    amount = statement_item["amount"] / 100  # Приведення до гривень
    balance = statement_item["balance"] / 100  # Приведення до гривень
    receipt_id = statement_item.get("receiptId", "")

    # Визначення типу повідомлення
    if amount > 0:
        message = (
            "✅ Зараз відбулось надходження!\n\n"
            f"📅 {formatted_date} 🕘 {formatted_time}\n"
            f"💳 {description}\n"
            f"💬 {comment}\n"
            f"💰 Сума: {amount:.2f}\n"
            f"💵 Баланс: {balance:.2f}\n"
            "〰〰〰〰〰〰〰"
        )
    else:
        message = (
            "🔻 Щойно були витрачені кошти!\n\n"
            f"📅 {formatted_date} 🕘 {formatted_time}\n"
            f"🛍 Кому: {description}\n"
            f"🧾  <a href=https://check.gov.ua/{receipt_id}>{receipt_id}</a>\n"
            f"💰 Сума: {amount:.2f}\n"
            f"💵 Залишок: {balance:.2f}\n"
            "〰〰〰〰〰〰〰"
        )
    print(message)
    return message

if __name__ == "__main__":
    pass
