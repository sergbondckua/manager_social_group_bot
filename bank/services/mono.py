import logging
from typing import NoReturn

import monobank

logger = logging.getLogger("monobank")


def setup_webhook(token: str, webhook_url: str) -> None:
    """Configure Monobank webhook."""
    mono_client = monobank.Client(token=token)

    try:
        client_info = mono_client.get_client_info()
        if not client_info.get("webHookUrl"):
            mono_client.create_webhook(url=webhook_url)
            logger.info("Webhook successfully created")
        else:
            logger.info("Webhook is already configured")
    except monobank.TooManyRequests as e:
        logger.error("Rate limit exceeded: %s. Retrying later...", e)
    except monobank.Error as e:
        logger.error("API error occurred: %s", e)


def get_id_creditcard(token: str) -> list:
    """Отримує ідентифікатор кредитного рахунку та деталі для вибору."""
    try:
        mono_client = monobank.Client(token=token)
        accounts = mono_client.get_client_info().get("accounts", [])
    except Exception as e:
        logger.error("Error occurred: %s", e)
        return []

    card_choices = []
    for account in accounts:
        account_id = account.get("id", "Unknown ID")
        account_type = account.get("type", "Unknown type")
        masked_pan = account.get("maskedPan", ["Unknown maskedPan"])

        card_choices.append(
            (account_id, f"{account_type} - {', '.join(masked_pan)}"),
        )

    return card_choices


def main() -> NoReturn:
    """Main application entry point."""
    client_info = get_id_creditcard(
        "bc76dftg7eyg4b3fnoij8y78t6fg"
    )
    print(client_info)


if __name__ == "__main__":
    main()
