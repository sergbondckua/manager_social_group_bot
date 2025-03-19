import asyncio
import logging
from typing import List, Optional
from aiogram import Bot
from aiogram.types import (
    FSInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from asgiref.sync import sync_to_async
from dateutil.relativedelta import relativedelta
from django.utils import timezone

from chronopost.enums import PeriodicityChoices
from chronopost.models import ScheduledMessage
from common.utils import clean_tag_message

logger = logging.getLogger("schedulers")


class MessageScheduler:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.now = timezone.now()

    @sync_to_async
    def fetch_scheduled_messages(self) -> List[ScheduledMessage]:
        """Отримує список активних запланованих повідомлень, час яких настав або минув."""
        messages = ScheduledMessage.objects.filter(
            scheduled_time__lte=self.now, is_active=True
        )
        count = messages.count()
        if count > 0:
            logger.info("Отримано %d повідомлень.", count)
        return list(messages)

    @staticmethod
    def _create_keyboard(
        message: ScheduledMessage,
    ) -> Optional[InlineKeyboardMarkup]:
        """Створює клавіатуру з кнопкою, якщо є текст і URL кнопки."""

        if message.button_text and message.button_url:
            return InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=message.button_text, url=message.button_url
                        )
                    ]
                ]
            )
        return None

    async def _send_single_message(self, message: ScheduledMessage) -> bool:
        """Відправляє одне повідомлення та повертає успішність операції."""

        try:
            keyboard = self._create_keyboard(message)
            if message.photo:
                await self.bot.send_chat_action(
                    chat_id=message.chat_id, action="upload_photo"
                )
                photo_file = FSInputFile(message.photo.path)
                await self.bot.send_photo(
                    chat_id=message.chat_id,
                    photo=photo_file,
                    caption=clean_tag_message(message.text)[:1024],
                    reply_markup=keyboard,
                )
            else:
                await self.bot.send_chat_action(
                    chat_id=message.chat_id, action="typing"
                )
                await self.bot.send_message(
                    chat_id=message.chat_id,
                    text=clean_tag_message(message.text)[:4096],
                    reply_markup=keyboard,
                )
            return True
        except Exception as e:
            logger.error(
                "Помилка надсилання повідомлення ID %s (chat ID: %s, text: %s): %s",
                message.id,
                message.chat_id,
                message.text,
                e,
            )
            return False

    async def send_messages(
        self, messages: List[ScheduledMessage]
    ) -> List[ScheduledMessage]:
        """Асинхронно надсилає повідомлення через Telegram-бота."""

        tasks = [self._send_single_message(msg) for msg in messages]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful = [
            msg for msg, result in zip(messages, results) if result is True
        ]
        failed = [
            msg for msg, result in zip(messages, results) if result is not True
        ]

        if successful:
            logger.info("Успішно надіслано %d повідомлень.", len(successful))
        if failed:
            logger.error("Не вдалося надіслати %d повідомлень.", len(failed))

        return successful

    async def update_periodic_messages(
        self, successful_messages: List[ScheduledMessage]
    ) -> None:
        """Оновлює час для успішно відправлених періодичних повідомлень."""
        periodic_updates = {
            PeriodicityChoices.DAILY: relativedelta(days=1),
            PeriodicityChoices.WEEKLY: relativedelta(weeks=1),
            PeriodicityChoices.MONTHLY: relativedelta(months=1),
        }

        for period, delta in periodic_updates.items():
            messages = [
                m for m in successful_messages if m.periodicity == period
            ]
            if messages:
                await self._update_messages(messages, delta)

        # Деактивація одноразових повідомлень
        one_time_messages = [
            m
            for m in successful_messages
            if m.periodicity == PeriodicityChoices.ONCE
        ]
        if one_time_messages:
            await self._deactivate_one_time_messages(one_time_messages)

    @sync_to_async
    def _update_messages(
        self, messages: List[ScheduledMessage], delta: relativedelta
    ) -> None:
        """Оновлює час для списку повідомлень з урахуванням дельти."""
        if not messages:
            return

        for msg in messages:
            msg.scheduled_time += delta
            while msg.scheduled_time <= self.now:
                msg.scheduled_time += delta

        ScheduledMessage.objects.bulk_update(
            messages, ["scheduled_time"], batch_size=500
        )
        logger.info(
            "Оновлено %d повідомлень з новими scheduled_time.", len(messages)
        )

    @sync_to_async
    def _deactivate_one_time_messages(
        self, messages: List[ScheduledMessage]
    ) -> None:
        """Деактивує одноразові повідомлення після надсилання."""
        if not messages:
            return

        ScheduledMessage.objects.filter(
            id__in=[msg.id for msg in messages]
        ).update(is_active=False)
        logger.info("Деактивовані %d разових повідомлень.", len(messages))

    async def process_messages(self) -> None:
        """Основний метод для обробки повідомлень."""
        logger.info("Початок обробки повідомлень...")
        self.now = timezone.now()
        messages = await self.fetch_scheduled_messages()
        if not messages:
            logger.info("Немає повідомлень для обробки.")
            return

        successful_messages = await self.send_messages(messages)
        if successful_messages:
            await self.update_periodic_messages(successful_messages)

        logger.info("Кінець обробки повідомлень.")
