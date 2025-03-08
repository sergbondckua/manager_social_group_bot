import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from common.models import BaseModel
from chronopost.enums import PeriodicityChoices


class ScheduledMessage(BaseModel):
    """Модель для збереження запланованих повідомлень."""

    def get_upload_path(self, filename):
        # Генерируем уникальное имя файла и возвращаем путь к нему

        file_extension = filename.split(".")[-1]
        new_filename = f"{uuid.uuid4().hex}.{file_extension}"
        return f"scheduled_messages/images/{abs(self.chat_id)}/{new_filename}"

    title = models.CharField(
        verbose_name="Назва повідомлення",
        max_length=100,
        help_text="Назва повідомлення або цільове призначення",
    )
    chat_id = models.BigIntegerField(
        verbose_name="ID чату",
        default=settings.DEFAULT_CHAT_ID,
        help_text="""ID чату, до якого будуть відправлятися повідомлення.
                  Увага: бот повинен бути доданий до вказаного чату, 
                  та якщо це ID користувача, він
                  повинен раніше взаємодіяти з ботом.
                  Інакше повідомлення не буде доставлено!""",
    )
    scheduled_time = models.DateTimeField(
        verbose_name="Час відправки",
        help_text="Час відправки повідомлення",
    )
    periodicity = models.CharField(
        max_length=10,
        choices=PeriodicityChoices.choices,
        verbose_name="Періодичність",
        help_text="Періодичність відправки повідомлення",
    )
    text = models.TextField(
        verbose_name="Текст повідомлення",
        help_text="Текст повідомлення",
    )
    button_text = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Текст кнопки",
        help_text="Текст, який відображатиметься на кнопці",
    )
    button_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Посилання для кнопки",
        help_text="Посилання, на яке буде вести кнопка",
    )
    photo = models.ImageField(
        upload_to=get_upload_path,
        blank=True,
        null=True,
        verbose_name="Фото",
        help_text="Завантажте зображення для повідомлення. Формати: .jpg, .jpeg, .png, .gif",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активне",
    )

    class Meta:
        verbose_name = "Планове сповіщення"
        verbose_name_plural = "📩 Планові сповіщення"

    def __str__(self):
        # Конвертуємо час у локальний часовий пояс
        local_time = timezone.localtime(self.scheduled_time)
        return (
            f"{self.title} заплановано на {local_time} для ID: {self.chat_id}"
        )


class WeatherNotification(BaseModel):
    """Модель для збереження сповіщень про погоду."""

    def get_upload_path(self, filename):
        # Генерируем уникальное имя файла и возвращаем путь к нему

        file_extension = filename.split(".")[-1]
        new_filename = f"{uuid.uuid4().hex}.{file_extension}"
        return f"scheduled_messages/images/{abs(self.chat_id)}/weather/{new_filename}"

    title = models.CharField(
        verbose_name="Назва / Цільове призначення", max_length=100
    )
    chat_id = models.BigIntegerField(
        verbose_name="Chat ID",
        default=settings.DEFAULT_CHAT_ID,
        unique=True,
    )
    text = models.TextField(
        verbose_name="Текст сповіщення", blank=True, null=True
    )
    poster = models.ImageField(
        verbose_name="Зображення для повідомлення",
        upload_to=get_upload_path,
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(verbose_name="Активне", default=True)

    def __str__(self):
        return f"Сповіщення для Chat ID: {self.chat_id}"

    class Meta:
        verbose_name = "Інформер опадів"
        verbose_name_plural = "🌂 Інформери опадів"
