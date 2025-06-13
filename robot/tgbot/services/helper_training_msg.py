import logging

from training_events.models import TrainingEvent, TrainingMessage

# Налаштування логування
logger = logging.getLogger("helper_training_msg")


async def save_training_message_info(
    training_id: int, chat_id: int, message_id: int
):
    """
    Зберігає інформацію про повідомлення з тренуванням

    Args:
        training_id: ID тренування
        chat_id: ID чату, де опубліковано повідомлення
        message_id: ID повідомлення
    """
    try:
        training = await TrainingEvent.objects.aget(id=training_id)
        await TrainingMessage.objects.acreate(
            training=training, chat_id=chat_id, message_id=message_id
        )
        logger.info(
            "Збережено інформацію про повідомлення для тренування %s: chat_id=%s, message_id=%s",
            training.title,
            chat_id,
            message_id,
        )
    except Exception as e:
        logger.error(
            "Помилка при збереженні інформації про повідомлення: %s", e
        )


async def update_training_message_info(
    training_id: int, chat_id: int, message_id: int
):
    """
    Оновлює інформацію про повідомлення з тренуванням

    Args:
        training_id: ID тренування
        chat_id: ID чату
        message_id: ID повідомлення
    """
    try:
        training = await TrainingEvent.objects.aget(id=training_id)
        training_message, created = (
            await TrainingMessage.objects.aget_or_create(
                training=training,
                defaults={"chat_id": chat_id, "message_id": message_id},
            )
        )

        if not created:
            training_message.chat_id = chat_id
            training_message.message_id = message_id
            await training_message.asave()

        logger.info(
            "Оновлено інформацію про повідомлення для тренування %s: chat_id=%s, message_id=%s",
            training.title,
            chat_id,
            message_id,
        )
    except Exception as e:
        logger.error(
            "Помилка при оновленні інформації про повідомлення: %s", e
        )


async def get_training_message_info(training_id: int):
    """
    Отримує інформацію про повідомлення з тренуванням

    Args:
        training_id: ID тренування

    Returns:
        tuple: (chat_id, message_id) або (None, None) якщо не знайдено
    """
    try:
        training = await TrainingEvent.objects.aget(id=training_id)
        training_message = await TrainingMessage.objects.aget(
            training=training
        )
        return training_message.chat_id, training_message.message_id
    except TrainingMessage.DoesNotExist:
        logger.warning(
            "Інформація про повідомлення не знайдена для тренування ID: %s",
            training_id,
        )
        return None, None
    except Exception as e:
        logger.error(
            "Помилка при отриманні інформації про повідомлення: %s", e
        )
        return None, None
