# Константи
from datetime import datetime

from aiogram.types import Message

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 100
MIN_LOCATION_LENGTH = 3
MAX_LOCATION_LENGTH = 150
MIN_DISTANCE = 1
MAX_DISTANCE = 100
MAX_PARTICIPANTS = 100
MIN_PACE_SECONDS = 180  # 3:00
MAX_PACE_SECONDS = 900  # 15:00


def validate_title(title: str) -> bool:
    """Валідує назву тренування."""
    return MIN_TITLE_LENGTH <= len(title.strip()) <= MAX_TITLE_LENGTH


def validate_location(location: str) -> bool:
    """Валідує місце проведення тренування."""
    return MIN_LOCATION_LENGTH <= len(location.strip()) <= MAX_LOCATION_LENGTH


def validate_distance(distance: float) -> bool:
    """Валідує дистанцію."""
    return MIN_DISTANCE < distance <= MAX_DISTANCE


def validate_participants(participants: int) -> bool:
    """Валідує кількість учасників."""
    return 0 <= participants <= MAX_PARTICIPANTS


def validate_pace(pace_str: str) -> bool:
    """Валідує темп."""
    try:
        parsed_pace = datetime.strptime(pace_str, "%M:%S").time()
        total_seconds = parsed_pace.minute * 60 + parsed_pace.second
        return MIN_PACE_SECONDS <= total_seconds <= MAX_PACE_SECONDS
    except ValueError:
        return False

# Перевірка, що повідомлення надійшло у приватному чаті
async def is_private_chat(message: Message) -> bool:
    return message.chat.type == "private"