from datetime import datetime
from typing import Optional


def parse_date(date_str: str) -> Optional[datetime]:
    """Парсить дату з рядка."""
    try:
        normalized_date = (
            date_str.strip()
            .replace("/", ".")
            .replace(",", ".")
            .replace(" ", ".")
        )
        return datetime.strptime(normalized_date, "%d.%m.%Y")
    except ValueError:
        return None


def parse_time(time_str: str) -> Optional[datetime]:
    """Парсить час з рядка."""
    try:
        normalized_time = (
            time_str.strip()
            .replace("/", ":")
            .replace(",", ":")
            .replace(" ", ":")
            .replace(".", ":")
        )
        return datetime.strptime(normalized_time, "%H:%M")
    except ValueError:
        return None


def parse_pace(pace_str: str) -> str:
    """Парсить та нормалізує темп."""
    return (
        pace_str.strip().replace(".", ":").replace(",", ":").replace(" ", ":")
    )
